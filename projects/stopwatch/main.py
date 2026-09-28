# 碼錶：OLED 128x64 顯示到百分之一秒，外接 LED 與停止按鈕
# 接線：
#   OLED  P20 -> SDA, P19 -> SCL, 3V -> VCC, GND -> GND
#   LED   P15 -> (限流電阻) -> 紅色 LED -> GND   計時中亮起
#   按鈕  P16 -> 按鈕 -> GND（按下為低電平，使用內部上拉）
# 操作：A 開始（LED 亮）、P16 按鈕停止（LED 滅）、A+B 同時按歸零
#       停止後再按 A 會接續計時
# 需要一起上傳 components/oled_ssd1306/ssd1306.py
from microbit import (i2c, pin15, pin16, pin19, pin20, display,
                      button_a, button_b, sleep, running_time)
from ssd1306 import SSD1306

COMBO_MS = 80      # 按下 A 後，等待 B 的時間（判斷是否為 A+B）
DEBOUNCE_MS = 20   # P16 需先穩定放開這麼久，才接受下一次按下（濾除按鈕彈跳）

led = pin15
stop_btn = pin16
led.write_digital(0)
stop_btn.set_pull(stop_btn.PULL_UP)


def i2c_setup():
    i2c.init(freq=400000, sda=pin20, scl=pin19)


i2c_setup()
oled = SSD1306(i2c, 0x3C, 128, 64)


def show(page_start, page_end):
    # show() 內部已重試；仍失敗時重新初始化 I2C，下一格畫面再試，計時不受影響
    if not oled.show(page_start, page_end):
        i2c_setup()


# ---- 按鍵偵測：記錄「按下的瞬間」，畫面更新中也會多次呼叫 ----
a_prev = False
a_t = None          # A 被按下的時間（尚未處理）
p16_prev = False
p16_high_since = 0  # P16 最近一次變回放開的時間
p16_t = None        # P16 被按下的時間（尚未處理）


def poll():
    global a_prev, a_t, p16_prev, p16_high_since, p16_t
    now = running_time()

    a = button_a.is_pressed()
    if a and not a_prev and a_t is None:
        a_t = now
    a_prev = a

    p = stop_btn.read_digital() == 0
    if p and not p16_prev:
        if now - p16_high_since >= DEBOUNCE_MS and p16_t is None:
            p16_t = now
    elif not p and p16_prev:
        p16_high_since = now
    p16_prev = p


# ---- 固定畫面 ----
oled.text("STOPWATCH", 0, 0)
oled.hline(0, 10, 128)
oled.hline(0, 45, 128)
oled.text("A:GO P16:STOP A+B:0", 0, 52)
oled.show()

running = False
elapsed = 0   # 停止時累計的毫秒數
start = 0     # 開始計時的 running_time()


def now_ms():
    return running_time() - start if running else elapsed


def draw_state():
    label = "RUN  " if running else ("STOP " if elapsed else "READY")
    oled.fill_rect(92, 0, 36, 8, 0)
    oled.text(label, 92, 0)
    show(0, 0)


def draw_time(ms):
    cs = ms // 10
    mm = (cs // 6000) % 100
    ss = (cs // 100) % 60
    oled.fill_rect(0, 16, 128, 22, 0)
    poll()
    oled.text("%02d:%02d" % (mm, ss), 1, 16, scale=3)       # 寬 90、高 21
    poll()
    oled.text(".%02d" % (cs % 100), 91, 23, scale=2)        # 與大字底部對齊
    poll()
    show(2, 4)                                             # 只更新數字所在的 page 2~4
    poll()


draw_state()
draw_time(0)
display.show("0")

while True:
    poll()

    if a_t is not None:
        t = a_t
        # 等一下，看 B 是否也被按下（A+B 歸零）；B 先按住再按 A 也算
        combo = button_b.is_pressed()
        while not combo and running_time() - t < COMBO_MS:
            poll()
            combo = button_b.is_pressed()
        if combo:
            running = False
            elapsed = 0
            led.write_digital(0)
            display.show("0")
            draw_state()
            draw_time(0)
            # 等兩顆鍵都放開，避免放開時又被當成按下 A
            while button_a.is_pressed() or button_b.is_pressed():
                sleep(10)
            a_prev = False
            p16_t = None
        elif not running:
            start = t - elapsed   # 以按下的瞬間為準，不含判斷 A+B 的等待時間
            running = True
            led.write_digital(1)
            display.show(">")
            draw_state()
        a_t = None

    if p16_t is not None:
        if running:
            elapsed = max(p16_t - start, 0)   # 以按下的瞬間為準
            running = False
            led.write_digital(0)
            display.show("=")
            draw_state()
            draw_time(elapsed)                 # 停止時顯示精確的最終值
        p16_t = None

    if running:
        draw_time(now_ms())
    else:
        sleep(5)
