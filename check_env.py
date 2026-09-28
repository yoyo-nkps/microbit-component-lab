r"""檢查 micro:bit 開發環境是否準備好。

用法：.venv\Scripts\python check_env.py
"""
import sys
import time

MICROBIT_VID = 0x0D28  # micro:bit (DAPLink) 的 USB Vendor ID

ok_count = 0
fail_count = 0


def report(ok, name, detail=""):
    global ok_count, fail_count
    if ok:
        ok_count += 1
    else:
        fail_count += 1
    mark = "[OK]  " if ok else "[FAIL]"
    print(f"{mark} {name}" + (f" - {detail}" if detail else ""))


# 1. Python 版本
v = sys.version_info
report(v[:2] >= (3, 10), "Python 版本", f"{v.major}.{v.minor}.{v.micro}")

# 2. 是否在虛擬環境中執行
in_venv = sys.prefix != sys.base_prefix
report(in_venv, "虛擬環境 (.venv)", sys.prefix if in_venv else "請用 .venv\\Scripts\\python 執行")

# 3. 必要套件
try:
    import serial
    import serial.tools.list_ports
    report(True, "pyserial", serial.__version__)
except ImportError:
    report(False, "pyserial", "請執行 pip install -r requirements.txt")
    serial = None

try:
    import microfs  # noqa: F401
    report(True, "microfs")
except ImportError:
    report(False, "microfs", "請執行 pip install -r requirements.txt")

# 4. 找 micro:bit 序列埠
port = None
if serial:
    for p in serial.tools.list_ports.comports():
        if p.vid == MICROBIT_VID:
            port = p.device
            break
    report(port is not None, "micro:bit USB 連線", port or "找不到，請檢查 USB 線（需可傳資料的線）")

# 5. 確認 micro:bit 上是否有 MicroPython
if port:
    try:
        with serial.Serial(port, 115200, timeout=1) as s:
            s.write(b"\x03\x03")  # Ctrl+C 中斷正在執行的程式，進入 REPL
            time.sleep(0.5)
            s.reset_input_buffer()
            s.write(b"import sys;print('IMPL='+sys.implementation.name)\r\n")
            time.sleep(0.8)
            out = s.read(s.in_waiting or 1).decode(errors="ignore")
        found = "IMPL=micropython" in out
        report(found, "micro:bit MicroPython 韌體",
               "有回應" if found else "沒回應，請到 python.microbit.org 下載 .hex 拖到 MICROBIT 磁碟")
    except serial.SerialException as e:
        report(False, "開啟序列埠", f"{e}（是否被 Thonny 或其他程式佔用？）")

print()
print(f"結果：{ok_count} 項通過，{fail_count} 項失敗")
sys.exit(1 if fail_count else 0)
