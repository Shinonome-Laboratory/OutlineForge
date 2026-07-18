"""一键终止：停止所有正在运行的 uvicorn 进程（02-outline 服务）。"""

import os
import signal
import subprocess
import sys

PROJECT_PORT = 8001
PROJECT_DISPLAY_NAME = "All for Style / 02-outline"
MAIN_MODULE = "main_outline:app"


def T(zh: str, ja: str, en: str) -> str:
    return f"{zh} / {ja} / {en}"


def M(zh: str, ja: str, en: str) -> str:
    return f"[ZH] {zh}\n[JA] {ja}\n[EN] {en}"


# 强制 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(PARENT_DIR, ".server.pid")

print("═" * 50)
print(M(
    f"  终止 {PROJECT_DISPLAY_NAME} 服务",
    f"  {PROJECT_DISPLAY_NAME} サービスを停止",
    f"  Stopping {PROJECT_DISPLAY_NAME} Service",
))
print("═" * 50)
print()

killed_any = False

# ---------------------------------------------------------------------------
# 方案 1：通过 PID 文件精确终止
# ---------------------------------------------------------------------------
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            print(T(
                f"✅ 已发送终止信号到 PID {pid}",
                f"✅ PID {pid} に終了シグナルを送信しました",
                f"✅ Sent termination signal to PID {pid}",
            ))
        except OSError:
            print(T(
                f"⚠️  PID {pid} 不存在，清理残留 PID 文件",
                f"⚠️  PID {pid} は存在しません。残留 PID ファイルを削除します",
                f"⚠️  PID {pid} not found, cleaning up stale PID file",
            ))
        os.remove(PID_FILE)
        killed_any = True
    except (ValueError, OSError) as e:
        print(T(
            f"⚠️  读取 PID 文件失败: {e}",
            f"⚠️  PID ファイルの読み取り失敗: {e}",
            f"⚠️  Failed to read PID file: {e}",
        ))

# ---------------------------------------------------------------------------
# 方案 2：按进程命令行匹配并终止 uvicorn
# wmic 在 Win11 24H2+ 已被移除（调用会静默失效），改用 PowerShell 的
# Get-CimInstance 一次性取回全部 python.exe 命令行。
# ---------------------------------------------------------------------------
try:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
         "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"],
        capture_output=True, text=True, timeout=15, errors="replace",
    )
    for line in (result.stdout or "").splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0].strip())
        except ValueError:
            continue
        cmdline = (parts[1] or "").lower()
        if ("uvicorn" in cmdline or MAIN_MODULE in cmdline) and pid != os.getpid():
            try:
                os.kill(pid, signal.SIGTERM)
                print(T(
                    f"✅ 已终止 uvicorn 进程 (PID {pid})",
                    f"✅ uvicorn プロセスを終了しました (PID {pid})",
                    f"✅ Killed uvicorn process (PID {pid})",
                ))
                killed_any = True
            except Exception:
                pass
except Exception:
    pass

# ---------------------------------------------------------------------------
# 方案 3：netstat 查找占用目标端口的进程
# ---------------------------------------------------------------------------
try:
    netstat_result = subprocess.run(
        ["netstat", "-ano", "-p", "TCP"],
        capture_output=True, text=True, timeout=10,
    )
    if netstat_result.returncode == 0:
        for line in netstat_result.stdout.split("\n"):
            if f":{PROJECT_PORT}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid_str = parts[-1]
                try:
                    pid = int(pid_str)
                    os.kill(pid, signal.SIGTERM)
                    print(T(
                        f"✅ 已终止占用端口 {PROJECT_PORT} 的进程 (PID {pid})",
                        f"✅ ポート {PROJECT_PORT} を使用中のプロセスを終了しました (PID {pid})",
                        f"✅ Killed process occupying port {PROJECT_PORT} (PID {pid})",
                    ))
                    killed_any = True
                except (ValueError, OSError):
                    pass
except Exception:
    pass

if not killed_any:
    print(M(
        "ℹ️  未找到正在运行的服务。",
        "ℹ️  実行中のサービスが見つかりません。",
        "ℹ️  No running service found.",
    ))

print()
print(M("  完毕。", "  完了。", "  Done."))
