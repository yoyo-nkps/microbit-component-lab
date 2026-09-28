# SSD1306 I2C OLED 驅動（micro:bit MicroPython 用，不依賴 framebuf）
# 支援：pixel / fill / hline / vline / line / rect / fill_rect / text / invert / show
import time

# 5x7 ASCII 字型（32~126），每字 5 bytes，一個 byte 為一欄，LSB 在上
FONT = (
    b"\x00\x00\x00\x00\x00\x00\x00\x5f\x00\x00\x00\x07\x00\x07\x00\x14\x7f\x14\x7f\x14"
    b"\x24\x2a\x7f\x2a\x12\x23\x13\x08\x64\x62\x36\x49\x55\x22\x50\x00\x05\x03\x00\x00"
    b"\x00\x1c\x22\x41\x00\x00\x41\x22\x1c\x00\x08\x2a\x1c\x2a\x08\x08\x08\x3e\x08\x08"
    b"\x00\x50\x30\x00\x00\x08\x08\x08\x08\x08\x00\x60\x60\x00\x00\x20\x10\x08\x04\x02"
    b"\x3e\x51\x49\x45\x3e\x00\x42\x7f\x40\x00\x42\x61\x51\x49\x46\x21\x41\x45\x4b\x31"
    b"\x18\x14\x12\x7f\x10\x27\x45\x45\x45\x39\x3c\x4a\x49\x49\x30\x01\x71\x09\x05\x03"
    b"\x36\x49\x49\x49\x36\x06\x49\x49\x29\x1e\x00\x36\x36\x00\x00\x00\x56\x36\x00\x00"
    b"\x08\x14\x22\x41\x00\x14\x14\x14\x14\x14\x00\x41\x22\x14\x08\x02\x01\x51\x09\x06"
    b"\x32\x49\x79\x41\x3e\x7e\x11\x11\x11\x7e\x7f\x49\x49\x49\x36\x3e\x41\x41\x41\x22"
    b"\x7f\x41\x41\x22\x1c\x7f\x49\x49\x49\x41\x7f\x09\x09\x01\x01\x3e\x41\x41\x51\x32"
    b"\x7f\x08\x08\x08\x7f\x00\x41\x7f\x41\x00\x20\x40\x41\x3f\x01\x7f\x08\x14\x22\x41"
    b"\x7f\x40\x40\x40\x40\x7f\x02\x04\x02\x7f\x7f\x04\x08\x10\x7f\x3e\x41\x41\x41\x3e"
    b"\x7f\x09\x09\x09\x06\x3e\x41\x51\x21\x5e\x7f\x09\x19\x29\x46\x46\x49\x49\x49\x31"
    b"\x01\x01\x7f\x01\x01\x3f\x40\x40\x40\x3f\x1f\x20\x40\x20\x1f\x7f\x20\x18\x20\x7f"
    b"\x63\x14\x08\x14\x63\x03\x04\x78\x04\x03\x61\x51\x49\x45\x43\x00\x7f\x41\x41\x00"
    b"\x02\x04\x08\x10\x20\x00\x41\x41\x7f\x00\x04\x02\x01\x02\x04\x40\x40\x40\x40\x40"
    b"\x00\x01\x02\x04\x00\x20\x54\x54\x54\x78\x7f\x48\x44\x44\x38\x38\x44\x44\x44\x20"
    b"\x38\x44\x44\x48\x7f\x38\x54\x54\x54\x18\x08\x7e\x09\x01\x02\x08\x14\x54\x54\x3c"
    b"\x7f\x08\x04\x04\x78\x00\x44\x7d\x40\x00\x20\x40\x44\x3d\x00\x00\x7f\x10\x28\x44"
    b"\x00\x41\x7f\x40\x00\x7c\x04\x18\x04\x78\x7c\x08\x04\x04\x78\x38\x44\x44\x44\x38"
    b"\x7c\x14\x14\x14\x08\x08\x14\x14\x18\x7c\x7c\x08\x04\x04\x08\x48\x54\x54\x54\x20"
    b"\x04\x3f\x44\x40\x20\x3c\x40\x40\x20\x7c\x1c\x20\x40\x20\x1c\x3c\x40\x30\x40\x3c"
    b"\x44\x28\x10\x28\x44\x0c\x50\x50\x50\x3c\x44\x64\x54\x4c\x44\x00\x08\x36\x41\x00"
    b"\x00\x00\x7f\x00\x00\x00\x41\x36\x08\x00\x08\x04\x08\x10\x08"
)


class SSD1306:
    def __init__(self, i2c, addr=0x3C, width=128, height=64):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.pages = height // 8
        # 每個 page 前面多放一個 0x40（I2C 資料前導 byte），show() 時可直接傳送、不必複製
        # 像素 (x, page) 位於 buf[page * stride + 1 + x]
        self.stride = width + 1
        self.buf = bytearray(self.stride * self.pages)
        mv = memoryview(self.buf)
        self._rows = []
        for p in range(self.pages):
            self.buf[p * self.stride] = 0x40
            self._rows.append(mv[p * self.stride:(p + 1) * self.stride])
        self.cmd(
            0xAE,              # 關閉顯示
            0x20, 0x00,        # 水平定址模式
            0x40,              # 起始行 0
            0xA1,              # 左右翻轉（column 127 對應 SEG0）
            0xA8, height - 1,  # multiplex ratio
            0xC8,              # 上下翻轉（COM 由下往上掃）
            0xD3, 0x00,        # 顯示偏移 0
            0xDA, 0x12 if height == 64 else 0x02,  # COM 腳位設定
            0xD5, 0x80,        # 時脈
            0xD9, 0xF1,        # pre-charge
            0xDB, 0x30,        # VCOMH
            0x81, 0xCF,        # 對比
            0xA4,              # 依 RAM 內容顯示
            0xA6,              # 正常（非反白）
            0xD6, 0x00,        # 關閉 zoom（MakeCode oled12864_i2c 會開啟，OLED 沒斷電會殘留）
            0x8D, 0x14,        # 開啟內部 charge pump
            0xAF,              # 開啟顯示
        )
        self.fill(0)
        self.show()

    def cmd(self, *cmds):
        self.i2c.write(self.addr, bytes((0x00,) + cmds))

    def show(self, page_start=0, page_end=None, retries=3):
        """把緩衝區送到螢幕。可只送部分 page（每 page 高 8 像素）以加快更新。

        I2C 偶爾會傳輸失敗（ENODEV/EIO），失敗時整批重送；
        重試後仍失敗回傳 False，不丟出例外，避免主程式中斷。
        """
        if page_end is None:
            page_end = self.pages - 1
        for _ in range(retries):
            try:
                self.cmd(0x21, 0, self.width - 1, 0x22, page_start, page_end)
                for p in range(page_start, page_end + 1):
                    self.i2c.write(self.addr, self._rows[p])
                return True
            except OSError:
                time.sleep_ms(2)
        return False

    def invert(self, on):
        self.cmd(0xA7 if on else 0xA6)

    def contrast(self, value):
        self.cmd(0x81, value & 0xFF)

    def power(self, on):
        self.cmd(0xAF if on else 0xAE)

    # ---- 繪圖 ----
    def fill(self, c):
        self.fill_rect(0, 0, self.width, self.height, c)

    def pixel(self, x, y, c=1):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y >> 3) * self.stride + 1 + x
            if c:
                self.buf[i] |= 1 << (y & 7)
            else:
                self.buf[i] &= ~(1 << (y & 7)) & 0xFF

    def hline(self, x, y, w, c=1):
        self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c=1):
        self.fill_rect(x, y, 1, h, c)

    def rect(self, x, y, w, h, c=1):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def fill_rect(self, x, y, w, h, c=1):
        # 以 page（直向 8 像素 = 1 byte）為單位整批處理，比逐點快很多
        x0 = max(x, 0)
        x1 = min(x + w, self.width)
        y0 = max(y, 0)
        y1 = min(y + h, self.height)
        if x0 >= x1 or y0 >= y1:
            return
        buf = self.buf
        for page in range(y0 >> 3, ((y1 - 1) >> 3) + 1):
            top = max(y0 - page * 8, 0)
            bot = min(y1 - page * 8, 8)
            mask = (0xFF << top) & (0xFF >> (8 - bot)) & 0xFF
            base = page * self.stride + 1
            if c:
                for i in range(base + x0, base + x1):
                    buf[i] |= mask
            else:
                inv = ~mask & 0xFF
                for i in range(base + x0, base + x1):
                    buf[i] &= inv

    def line(self, x0, y0, x1, y1, c=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.pixel(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def text(self, s, x, y, c=1, scale=1):
        """畫 ASCII 字串，每字寬 6*scale、高 8*scale。"""
        buf = self.buf
        w = self.width
        page0 = y >> 3
        shift = y & 7
        ones = (1 << scale) - 1
        for ch in s:
            o = ord(ch)
            if o < 32 or o > 126:
                o = 63  # 不支援的字元顯示 '?'
            base = (o - 32) * 5
            for col in range(5):
                bits = FONT[base + col]
                # 把這一欄 7 個像素垂直放大 scale 倍，再整批寫進各 page
                v = 0
                row = 0
                while bits:
                    if bits & 1:
                        v |= ones << (row * scale)
                    bits >>= 1
                    row += 1
                v <<= shift
                page = page0
                while v and page < self.pages:
                    b = v & 0xFF
                    if b and page >= 0:
                        i0 = page * self.stride + 1
                        for px in range(x + col * scale, x + col * scale + scale):
                            if 0 <= px < w:
                                if c:
                                    buf[i0 + px] |= b
                                else:
                                    buf[i0 + px] &= ~b & 0xFF
                    v >>= 8
                    page += 1
            x += 6 * scale
