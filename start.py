"""一键启动：先停止旧服务，再运行服务并自动打开浏览器。

用法:
    python start.py              # 启动前运行环境检查（仅报告）
    python start.py --fix        # 启动前自动修复环境问题
    python start.py --no-check   # 跳过环境检查直接启动
"""

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent
PROJECT_DISPLAY_NAME = "All for Style / 02-outline"
PORT = 8001
HOST = "0.0.0.0"
URL = f"http://127.0.0.1:{PORT}"
PID_FILE = PROJECT_ROOT / ".server.pid"
MAIN_MODULE = "main_outline:app"

AUTO_FIX = "--fix" in sys.argv
SKIP_CHECK = "--no-check" in sys.argv


def T(zh: str, ja: str, en: str) -> str:
    return f"{zh} / {ja} / {en}"


def M(zh: str, ja: str, en: str) -> str:
    return f"[ZH] {zh}\n[JA] {ja}\n[EN] {en}"


def _header(title_zh: str, title_ja: str, title_en: str):
    print("═" * 50)
    print(f"  [ZH] {title_zh}")
    print(f"  [JA] {title_ja}")
    print(f"  [EN] {title_en}")
    print("═" * 50)


# =============================================================================
# 内联 Stop 逻辑
# =============================================================================

def stop_old_service():
    """终止可能正在运行的旧服务进程。"""
    killed_any = False

    # 方案 1：PID 文件
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            try:
                os.kill(old_pid, signal.SIGTERM)
                print(T(
                    f"   ✅ 已终止旧进程 PID {old_pid}",
                    f"   ✅ 古いプロセス PID {old_pid} を終了しました",
                    f"   ✅ Killed old process PID {old_pid}",
                ))
                killed_any = True
            except OSError:
                print(T(
                    f"   ⚠️  PID {old_pid} 已不存在",
                    f"   ⚠️  PID {old_pid} は既に存在しません",
                    f"   ⚠️  PID {old_pid} no longer exists",
                ))
            PID_FILE.unlink()
        except (ValueError, OSError) as e:
            print(T(
                f"   ⚠️  读取 PID 文件失败: {e}",
                f"   ⚠️  PID ファイルの読み取り失敗: {e}",
                f"   ⚠️  Failed to read PID file: {e}",
            ))

    # 方案 2：tasklist + wmic
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.replace('"', "").split(",")
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1].strip())
                    except ValueError:
                        continue
                    try:
                        cmd_result = subprocess.run(
                            ["wmic", "process", "where", f"ProcessId={pid}",
                             "get", "CommandLine"],
                            capture_output=True, text=True, timeout=5,
                        )
                        cmdline = cmd_result.stdout.lower()
                        if ("uvicorn" in cmdline or MAIN_MODULE in cmdline) and pid != os.getpid():
                            os.kill(pid, signal.SIGTERM)
                            print(T(
                                f"   ✅ 已终止 uvicorn 进程 PID {pid}",
                                f"   ✅ uvicorn プロセス PID {pid} を終了しました",
                                f"   ✅ Killed uvicorn process PID {pid}",
                            ))
                            killed_any = True
                    except Exception:
                        pass
    except Exception:
        pass

    # 方案 3：netstat
    try:
        netstat_result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True, text=True, timeout=10,
        )
        if netstat_result.returncode == 0:
            for line in netstat_result.stdout.split("\n"):
                if f":{PORT}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    try:
                        pid = int(parts[-1])
                        if pid != os.getpid():
                            os.kill(pid, signal.SIGTERM)
                            print(T(
                                f"   ✅ 已终止占用端口 {PORT} 的进程 PID {pid}",
                                f"   ✅ ポート {PORT} を使用中のプロセス PID {pid} を終了しました",
                                f"   ✅ Killed process PID {pid} occupying port {PORT}",
                            ))
                            killed_any = True
                    except (ValueError, OSError):
                        pass
    except Exception:
        pass

    if killed_any:
        time.sleep(1.0)
        print()


# =============================================================================
# 主流程
# =============================================================================

_header(
    f"{PROJECT_DISPLAY_NAME} 启动中…",
    f"{PROJECT_DISPLAY_NAME} 起動中…",
    f"{PROJECT_DISPLAY_NAME} Starting…",
)
print()
print(M(
    f"后端地址: {URL}",
    f"バックエンドURL: {URL}",
    f"Backend URL: {URL}",
))
print(M(
    "按 Ctrl+C 停止服务",
    "Ctrl+C でサービスを停止",
    "Press Ctrl+C to stop service",
))
print()

# ---------------------------------------------------------------------------
# 先跑环境检查
# ---------------------------------------------------------------------------
check_script = PROJECT_ROOT / "setup.py"
if check_script.exists() and not SKIP_CHECK:
    args = [sys.executable, str(check_script)]
    if AUTO_FIX:
        args.append("--fix")
    else:
        args.append("--check-only")

    print(M(
        ">>> 运行环境检查…",
        ">>> 環境チェックを実行中…",
        ">>> Running environment check…",
    ))
    result = subprocess.run(args, capture_output=False)

    if result.returncode != 0:
        print()
        if not AUTO_FIX:
            print(M(
                "⚠️  环境检查有未通过项。",
                "⚠️  環境チェックに不合格項目があります。",
                "⚠️  Environment check has failed items.",
            ))
            print(f"   python setup.py --fix    {T('自动修复', '自動修復', 'auto-fix')}")
            print(f"   python start.py --fix    {T('修复并启动', '修復して起動', 'fix and start')}")
            print(f"   python start.py --no-check   {T('跳过检查直接启动', 'チェックをスキップして起動', 'skip check and start')}")
            print()
            try:
                ans = input(M(
                    "   是否仍要继续启动？ [y/N]: ",
                    "   それでも起動を続けますか？ [y/N]: ",
                    "   Continue to start anyway? [y/N]: ",
                )).strip().lower()
                if ans not in ("y", "yes"):
                    print(M(">>> 已取消。", ">>> キャンセルしました。", ">>> Cancelled."))
                    sys.exit(1)
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(1)
        else:
            print(M(
                "⚠️  部分问题无法自动修复，请手动处理后重试。",
                "⚠️  一部の問題は自動修復できません。手動で対応して再試行してください。",
                "⚠️  Some issues cannot be auto-fixed, please handle manually and retry.",
            ))
            sys.exit(result.returncode)

# ---------------------------------------------------------------------------
# 停止旧服务
# ---------------------------------------------------------------------------
print(M(
    ">>> 检查并停止旧服务…",
    ">>> 古いサービスをチェックして停止中…",
    ">>> Checking and stopping old service…",
))
stop_old_service()

# ---------------------------------------------------------------------------
# 启动服务
# ---------------------------------------------------------------------------
print(M(
    f">>> 启动服务 (uvicorn {MAIN_MODULE} --host {HOST} --port {PORT})…",
    f">>> サービスを起動中 (uvicorn {MAIN_MODULE} --host {HOST} --port {PORT})…",
    f">>> Starting service (uvicorn {MAIN_MODULE} --host {HOST} --port {PORT})…",
))
print()

proc = subprocess.Popen(
    [
        sys.executable, "-m", "uvicorn",
        MAIN_MODULE,
        f"--host={HOST}",
        f"--port={PORT}",
    ],
    cwd=str(PROJECT_ROOT),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
)

PID_FILE.write_text(str(proc.pid))

# ---------------------------------------------------------------------------
# 等待服务器就绪后打开浏览器
# ---------------------------------------------------------------------------
browser_opened = False
try:
    for line in proc.stdout:
        print(line, end="")
        if not browser_opened and "Uvicorn running on" in line:
            time.sleep(0.5)
            print(M(
                f"\n>>> 打开浏览器 → {URL}",
                f"\n>>> ブラウザを開く → {URL}",
                f"\n>>> Opening browser → {URL}",
            ))
            print()
            webbrowser.open(URL)
            browser_opened = True
except KeyboardInterrupt:
    print(M(
        "\n>>> 收到停止信号，正在关闭…",
        "\n>>> 停止信号を受信、シャットダウン中…",
        "\n>>> Received stop signal, shutting down…",
    ))
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    if PID_FILE.exists():
        PID_FILE.unlink()
    print(M(
        ">>> 服务已停止。",
        ">>> サービスが停止しました。",
        ">>> Service stopped.",
    ))
    sys.exit(0)
