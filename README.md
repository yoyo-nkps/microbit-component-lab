# micro:bit Component Lab

用 MicroPython 在 micro:bit V2 上驗證各種電子零件的練習專案。

## 專案結構

| 路徑 | 說明 |
|---|---|
| `components/oled_ssd1306/ssd1306.py` | SSD1306 I2C OLED 驅動（不依賴 `framebuf`，內建 5x7 字型，支援部分更新與 I2C 失敗自動重試） |
| `components/oled_ssd1306/main.py` | OLED 128x64 顯示範例 |
| `projects/stopwatch/main.py` | 碼錶：OLED 顯示到百分之一秒，外接 LED 與停止按鈕 |
| `check_env.py` | 檢查開發環境與 micro:bit 連線 |

## 環境準備（Windows）

1. 安裝 Python 3.12（只裝給目前使用者）：
   ```powershell
   winget install Python.Python.3.12 --scope user
   ```
2. 建立虛擬環境並安裝工具：
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python -m pip install -r requirements.txt
   ```
3. 燒入 MicroPython 韌體：從
   [micropython-microbit-v2 releases](https://github.com/microbit-foundation/micropython-microbit-v2/releases)
   下載 `micropython-microbit-v2.1.2.hex`，拖到 `MICROBIT` 磁碟。
4. 檢查環境：
   ```powershell
   .\.venv\Scripts\python check_env.py
   ```

## 上傳程式

```powershell
.\.venv\Scripts\ufs.exe put components\oled_ssd1306\ssd1306.py ssd1306.py
.\.venv\Scripts\ufs.exe put projects\stopwatch\main.py main.py
```

上傳後按 micro:bit 背面的 reset 鍵執行。micro:bit 開機只會自動執行 `main.py`。

上傳前請先關閉瀏覽器中 MakeCode / python.microbit.org 的 WebUSB 連線，否則會出現 `Could not enter raw REPL`。

## 接線

| 零件 | micro:bit |
|---|---|
| OLED SDA / SCL / VCC / GND | P20 / P19 / 3V / GND |
| 紅色 LED（串 220Ω 電阻）| P15 → LED → GND |
| 按鈕（按下為低電平） | P16 → 按鈕 → GND（使用內部上拉） |

## 碼錶操作

- **A**：開始計時（P15 LED 亮），停止後再按會接續計時
- **P16 按鈕**：停止（LED 滅）
- **A+B**：歸零

## 注意事項

- 若 OLED 之前跑過 MakeCode 擴充套件 `oled12864_i2c`，它會開啟 SSD1306 的 zoom 模式（`0xD6`），
  在 OLED 斷電前會一直保留，造成只顯示上半部且被拉長。本驅動初始化時會自動關閉。
