"""一键检查 + 一键安装配置运行环境。

用法:
    python setup.py              # 检查并逐一询问修复
    python setup.py --fix        # 检查并自动修复（不询问）
    python setup.py --check-only # 仅检查，不修复
"""

import importlib
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT.parent / "00-data"
DB_PATH = DATA_DIR / "corpus.db"

AUTO_FIX = "--fix" in sys.argv or "-y" in sys.argv
CHECK_ONLY = "--check-only" in sys.argv
INTERACTIVE = not AUTO_FIX and not CHECK_ONLY


def T(zh: str, ja: str, en: str) -> str:
    return f"{zh} / {ja} / {en}"


def M(zh: str, ja: str, en: str) -> str:
    return f"[ZH] {zh}\n[JA] {ja}\n[EN] {en}"


def ask_yn(prompt_zh: str, prompt_ja: str, prompt_en: str) -> bool:
    if AUTO_FIX:
        return True
    if CHECK_ONLY:
        return False
    try:
        prompt = f"   {prompt_zh} / {prompt_ja} / {prompt_en} [Y/n]: "
        ans = input(prompt).strip().lower()
        return ans in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def run(cmd: list[str], desc: str) -> bool:
    print(f"   ⏳ {desc}…")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"   ✅ {desc} — {T('完成', '完了', 'Done')}")
            return True
        else:
            stderr = result.stderr.strip()[:200]
            print(f"   ❌ {desc} — {T('失败', '失敗', 'Failed')}: {stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ❌ {desc} — {T('超时', 'タイムアウト', 'Timeout')}")
        return False
    except Exception as exc:
        print(f"   ❌ {desc} — {T('异常', 'エラー', 'Error')}: {exc}")
        return False


def check_port(port: int) -> tuple[bool, str, int | None]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex(("127.0.0.1", port))
        if result != 0:
            return True, T(
                f"端口 {port} 空闲",
                f"ポート {port} は空き",
                f"Port {port} free",
            ), None
        pid = None
        try:
            netstat = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True, timeout=5,
            )
            for line in netstat.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid_str = parts[-1]
                    if pid_str.isdigit():
                        pid = int(pid_str)
        except Exception:
            pass
        return False, T(
            f"端口 {port} 已被占用",
            f"ポート {port} は使用中",
            f"Port {port} in use",
        ) + (f" (PID {pid})" if pid else ""), pid
    finally:
        sock.close()


CHECKS: list[dict] = []


def register(status: str, name: str, detail: str = "", fix: str | None = None):
    CHECKS.append({"status": status, "name": name, "detail": detail, "fix": fix})


def failures():
    return [c for c in CHECKS if c["status"] == "FAIL"]


def warnings():
    return [c for c in CHECKS if c["status"] == "WARN"]


# ===========================================================================
# 阶段 1：收集所有检查结果
# ===========================================================================

# --- 1. Python 版本 ---
py_ok = sys.version_info >= (3, 10)
register("OK" if py_ok else "FAIL",
         "Python ≥ 3.10",
         f"{T('当前', '現在', 'Current')} {sys.version.split()[0]}",
         None)

# --- 2. pip ---
try:
    subprocess.run([sys.executable, "-m", "pip", "--version"],
                   capture_output=True, timeout=10, check=True)
    register("OK",
             T("pip 包管理器", "pip パッケージマネージャー", "pip package manager"),
             T("pip 可用", "pip 利用可能", "pip available"))
except Exception:
    register("FAIL",
             T("pip 包管理器", "pip パッケージマネージャー", "pip package manager"),
             T("pip 不可用，无法安装依赖", "pip 利用不可、依存関係をインストールできません",
                "pip unavailable, cannot install dependencies"),
             None)

# --- 3. 必需 Python 包 ---
REQUIRED_PACKAGES = {
    "fastapi": ("FastAPI", "fastapi"),
    "uvicorn": ("ASGI", "uvicorn"),
    "httpx": ("HTTP", "httpx"),
}
for pkg, (desc, pip_name) in REQUIRED_PACKAGES.items():
    try:
        importlib.import_module(pkg)
        register("OK", f"{desc}",
                 T(f"已安装 {pkg}", f"インストール済み {pkg}", f"Installed {pkg}"))
    except ImportError:
        register("FAIL", f"{desc}",
                 T(f"缺少 {pkg}", f"{pkg} が見つかりません", f"Missing {pkg}"),
                 f"pip:{pip_name}")

# --- 4. 外部工具 ---
EXTERNAL_TOOLS = {}
for tool, desc in EXTERNAL_TOOLS.items():
    if shutil.which(tool):
        register("OK", desc,
                 T(f"路径: {shutil.which(tool)}", f"パス: {shutil.which(tool)}",
                    f"Path: {shutil.which(tool)}"))
    else:
        register("FAIL", desc,
                 T(f"未找到 {tool}", f"{tool} が見つかりません", f"{tool} not found"),
                 f"winget:{desc}")

# --- 5. 本地模块 ---
try:
    import main_outline  # noqa: F401
    register("OK",
             T("main_outline 模块", "main_outline モジュール", "main_outline module"),
             T("main_outline.py 可导入", "main_outline.py インポート可能", "main_outline.py importable"))
except ImportError:
    register("FAIL",
             T("main_outline 模块", "main_outline モジュール", "main_outline module"),
             T("main_outline.py 导入失败", "main_outline.py インポート失敗",
                "main_outline.py import failed"),
             None)

# --- 6. 前端文件 ---
html_path = PROJECT_ROOT / "outline.html"
if html_path.is_file():
    register("OK",
             T("前端页面 outline.html", "フロントエンド outline.html", "Frontend outline.html"),
             str(html_path))
else:
    register("FAIL",
             T("前端页面 outline.html", "フロントエンド outline.html", "Frontend outline.html"),
             T("文件不存在", "ファイルが存在しません", "File not found"),
             None)

# --- 7. 数据库 ---
if DB_PATH.exists():
    register("OK",
             T("数据库 corpus.db", "データベース corpus.db", "Database corpus.db"),
             str(DB_PATH))
else:
    register("FAIL",
             T("数据库 corpus.db", "データベース corpus.db", "Database corpus.db"),
             T("文件不存在", "ファイルが存在しません", "File not found"),
             None)

# --- 8. 端口 8001 ---
PROJECT_PORT = 8001
port_ok, port_msg, port_pid = check_port(PROJECT_PORT)
register("OK" if port_ok else "WARN",
         T(f"端口 {PROJECT_PORT}", f"ポート {PROJECT_PORT}", f"Port {PROJECT_PORT}"),
         port_msg,
         f"portkill:{port_pid}" if port_pid else None)

# --- 9. Ollama 服务 ---
try:
    import httpx
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=3.0)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models]
            register("OK",
                     T("Ollama 服务", "Ollama サービス", "Ollama Service"),
                     T(f"运行中 · 模型: {', '.join(model_names[:5])}",
                       f"実行中 · モデル: {', '.join(model_names[:5])}",
                       f"Running · Models: {', '.join(model_names[:5])}"))
        else:
            register("WARN",
                     T("Ollama 服务", "Ollama サービス", "Ollama Service"),
                     T("响应异常（LLM 分析可能失败）",
                       "応答異常（LLM分析が失敗する可能性があります）",
                       "Abnormal response (LLM analysis may fail)"))
    except Exception:
        register("WARN",
                 T("Ollama 服务", "Ollama サービス", "Ollama Service"),
                 T("未检测到（LLM 分析不可用）",
                   "検出されません（LLM分析利用不可）",
                   "Not detected (LLM analysis unavailable)"))
except ImportError:
    register("WARN",
             T("Ollama 服务", "Ollama サービス", "Ollama Service"),
             T("httpx 未安装，无法检测", "httpx 未インストール、検出不可",
                "httpx not installed, cannot detect"))


# ===========================================================================
# 阶段 2：输出报告
# ===========================================================================

def _header(title_zh: str, title_ja: str, title_en: str):
    print()
    print("═" * 60)
    print(f"  [ZH] {title_zh}")
    print(f"  [JA] {title_ja}")
    print(f"  [EN] {title_en}")
    print("═" * 60)


def print_report():
    _header(
        "环境检查报告 — All for Style / 02-outline",
        "環境チェックレポート — All for Style / 02-outline",
        "Environment Check Report — All for Style / 02-outline",
    )

    for c in CHECKS:
        icon = {"OK": "  ✅", "WARN": "  ⚠️", "FAIL": "  ❌"}[c["status"]]
        print(f"{icon}  {c['name']}")
        if c["detail"]:
            print(f"       {c['detail']}")

    print("═" * 60)

    fail_count = len(failures())
    warn_count = len(warnings())

    if fail_count:
        print(f"\n❌ {fail_count} {T('项检查未通过，需要修复', '項目が不合格、修正が必要です', 'item(s) failed, fix required')}")
    if warn_count:
        print(f"⚠️  {warn_count} {T('项警告', '項目の警告', 'warning(s)')}")
    if not fail_count and not warn_count:
        print(f"\n✅ {T('所有检查通过，环境就绪', 'すべてのチェック合格、環境準備完了', 'All checks passed, environment ready')}")


# ===========================================================================
# 阶段 3：自动修复
# ===========================================================================

def do_fix():
    fail_list = failures()
    warn_list = warnings()
    fixable = [c for c in fail_list + warn_list if c["fix"]]

    if not fixable:
        return

    pip_pkgs = [c for c in fixable if c["fix"].startswith("pip:")]
    mkdirs = [c for c in fixable if c["fix"].startswith("mkdir:")]
    port_kills = [c for c in fixable if c["fix"].startswith("portkill:")]
    winget_items = [c for c in fixable if c["fix"].startswith("winget:")]

    _header("自动修复", "自動修復", "Auto-Fix")

    fixed_count = 0

    # --- pip 安装 ---
    if pip_pkgs:
        pkgs = [c["fix"].split(":", 1)[1] for c in pip_pkgs]
        names = [c["name"] for c in pip_pkgs]
        print(f"\n  📦 {T('Python 包', 'Python パッケージ', 'Python packages')}: {', '.join(names)}")
        if ask_yn(f"执行 pip install {' '.join(pkgs)} ?",
                  f"pip install {' '.join(pkgs)} を実行しますか？",
                  f"Run pip install {' '.join(pkgs)}?"):
            cmd = [
                sys.executable, "-m", "pip", "install",
                "--quiet", "--disable-pip-version-check",
            ] + pkgs
            ok = run(cmd, f"pip install {' '.join(pkgs)}")
            if ok:
                for c in pip_pkgs:
                    c["status"] = "OK"
                    c["detail"] = T(
                        f"已安装 {c['fix'].split(':',1)[1]}",
                        f"インストール済み {c['fix'].split(':',1)[1]}",
                        f"Installed {c['fix'].split(':',1)[1]}",
                    )
                    fixed_count += 1

    # --- 创建目录 ---
    for c in mkdirs:
        dir_path = Path(c["fix"].split(":", 1)[1])
        if ask_yn(f"创建目录 {dir_path} ?",
                  f"ディレクトリ {dir_path} を作成しますか？",
                  f"Create directory {dir_path}?"):
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                c["status"] = "OK"
                c["detail"] = T(f"已创建: {dir_path}", f"作成済み: {dir_path}", f"Created: {dir_path}")
                print(f"   ✅ {T('已创建', '作成済み', 'Created')} {dir_path}")
                fixed_count += 1
            except OSError as exc:
                print(f"   ❌ {T('创建失败', '作成失敗', 'Create failed')}: {exc}")

    # --- 释放端口 ---
    for c in port_kills:
        pid_str = c["fix"].split(":", 1)[1]
        pid = int(pid_str) if pid_str.isdigit() else None
        if pid and ask_yn(f"终止占用端口 {PROJECT_PORT} 的进程 PID {pid} ?",
                          f"ポート {PROJECT_PORT} を使用中のプロセス PID {pid} を終了しますか？",
                          f"Kill process PID {pid} occupying port {PROJECT_PORT}?"):
            try:
                import signal
                os.kill(pid, signal.SIGTERM)
                print(f"   ✅ {T('已终止 PID', 'PID 終了済み', 'Killed PID')} {pid}")
                c["status"] = "OK"
                c["detail"] = T(f"已释放端口 {PROJECT_PORT}", f"ポート {PROJECT_PORT} 解放済み", f"Port {PROJECT_PORT} released")
                fixed_count += 1
            except OSError as exc:
                print(f"   ❌ {T('终止失败', '終了失敗', 'Kill failed')}: {exc}")

    # --- winget 安装 ---
    if winget_items:
        names = [c["name"] for c in winget_items]
        ff_ok = shutil.which("winget") is not None
        if ff_ok:
            print(f"\n  🔧 {T('系统工具', 'システムツール', 'System tools')}: {', '.join(names)}")
            if ask_yn(f"使用 winget 安装 {' '.join(names)} ?",
                      f"winget で {' '.join(names)} をインストールしますか？",
                      f"Install {' '.join(names)} via winget?"):
                for c in winget_items:
                    tool_name = c["fix"].split(":", 1)[1]
                    run(["winget", "install", tool_name, "--accept-source-agreements"],
                        f"winget install {tool_name}")
                for c in winget_items:
                    tool_name = c["fix"].split(":", 1)[1]
                    exe_name = tool_name.lower().replace(" ", "")
                    if shutil.which(exe_name):
                        c["status"] = "OK"
                        c["detail"] = T(f"路径: {shutil.which(exe_name)}", f"パス: {shutil.which(exe_name)}", f"Path: {shutil.which(exe_name)}")
                        fixed_count += 1
        else:
            print(f"\n  🔧 {', '.join(names)} — {T('请手动安装', '手動でインストールしてください', 'Please install manually')}")

    if fixed_count:
        print(f"\n  ✅ {T(f'已修复 {fixed_count} 项', f'{fixed_count} 項目を修正しました', f'{fixed_count} item(s) fixed')}")

    # 重新验证 pip 包
    if pip_pkgs:
        print(f"\n  🔄 {T('重新验证 Python 包…', 'Python パッケージを再検証…', 'Re-verifying Python packages…')}")
        for c in pip_pkgs:
            pkg_name = c["fix"].split(":", 1)[1].replace("-", "_")
            try:
                importlib.import_module(pkg_name)
                c["status"] = "OK"
            except ImportError:
                c["status"] = "FAIL"

    # 最终报告
    _header("最终状态", "最終状態", "Final Status")
    for c in CHECKS:
        icon = {"OK": "  ✅", "WARN": "  ⚠️", "FAIL": "  ❌"}[c["status"]]
        print(f"{icon}  {c['name']}")
        if c["detail"]:
            print(f"       {c['detail']}")
    print("═" * 60)

    remaining_fail = len(failures())
    if remaining_fail:
        print(f"\n❌ {remaining_fail} {T('项仍未通过。请手动处理上述 ❌ 项后重试。', '項目がまだ不合格です。上記の❌項目を手動で対応して再試行してください。', 'item(s) still failed. Please handle ❌ items above manually and retry.')}")
        print(f"   python setup.py --fix   {T('可再次尝试自动修复', 'で再び自動修正を試行', 'to retry auto-fix')}")
        sys.exit(1)
    else:
        print(f"\n✅ {T('环境就绪，可以运行 python start.py 启动服务', '環境準備完了、python start.py でサービスを起動できます', 'Environment ready, run python start.py to start service')}")
        sys.exit(0)


# ===========================================================================
# 主入口
# ===========================================================================

if __name__ == "__main__":
    print_report()

    fail_list = failures()
    warn_list = warnings()

    if not fail_list and not warn_list:
        sys.exit(0)

    if CHECK_ONLY:
        if fail_list:
            sys.exit(1)
        sys.exit(0)

    fixable = [c for c in fail_list + warn_list if c["fix"]]
    if fixable:
        if AUTO_FIX:
            do_fix()
        else:
            print()
            if ask_yn("是否自动修复以上问题？",
                      "上記の問題を自動修正しますか？",
                      "Auto-fix the above issues?"):
                do_fix()
            else:
                print(f"\n{T('可以稍后运行 python setup.py --fix 进行自动修复', '後で python setup.py --fix で自動修正を実行できます', 'You can run python setup.py --fix later for auto-fix')}")
                if fail_list:
                    sys.exit(1)
                sys.exit(0)
    else:
        if fail_list:
            print(f"\n{T('无可自动修复的项，请手动处理上述 ❌ 项', '自動修正可能な項目がありません。上記の❌項目を手動で対応してください', 'No auto-fixable items, please handle ❌ items above manually')}")
            sys.exit(1)
        sys.exit(0)
