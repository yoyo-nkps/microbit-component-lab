# I2C OLED 128x64 (SSD1306) 顯示範例
# 接線：P20 -> SDA, P19 -> SCL, 3V -> VCC, GND -> GND
# 按 A：切換反白；按 B：歸零計時
from microbit import i2c, pin19, pin20, display, button_a, button_b, temperature, sleep, running_time
from ssd1306 import SSD1306

WIDTH = 128
HEIGHT = 64

i2c.init(freq=400000, sda=pin20, scl=pin19)

print("I2C scan:", [hex(a) for a in i2c.scan()])

# 直接寫一個 NOP 指令偵測位址（部分 SSD1306 不回應 scan）
addr = None
for a in (0x3C, 0x3D):
    try:
        i2c.write(a, b"\x00\xE3")
        addr = a
        break
    except OSError:
        pass
print("OLED addr:", hex(addr) if addr else None)
if addr is None:
    # 找不到 OLED：在 micro:bit LED 上提示，方便不接電腦也能除錯
    while True:
        display.scroll("NO OLED")

display.show("O")
oled = SSD1306(i2c, addr, WIDTH, HEIGHT)

# ---- 固定畫面 ----
oled.rect(0, 0, WIDTH, HEIGHT)
oled.text("micro:bit", 10, 4, scale=2)
oled.hline(0, 21, WIDTH)
oled.text("OLED 128x64 @" + hex(addr), 4, 25)
oled.show()

inverted = False
start = running_time()

while True:
    if button_a.was_pressed():
        inverted = not inverted
        oled.invert(inverted)
    if button_b.was_pressed():
        start = running_time()

    sec = (running_time() - start) // 1000

    # 清掉動態區域再重畫
    oled.fill_rect(1, 35, WIDTH - 2, 28, 0)
    oled.text("Temp: %d C" % temperature(), 4, 36)
    oled.text("Time: %d s" % sec, 4, 46)

    # 進度條：每 10 秒跑滿一次
    oled.rect(4, 56, 120, 6)
    oled.fill_rect(6, 58, (sec % 10 + 1) * 116 // 10, 2)

    oled.show()
    sleep(200)
