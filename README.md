# ️ 樹莓派即時溫度監控系統 (高效版)

[![Python Version](https://img.shields.io/badge/python-3.0+-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-latest-green.svg)](https://flask.palletsprojects.com/en/latest/)
[![SQLite Version](https://img.shields.io/badge/sqlite-latest-yellow.svg)](https://www.sqlite.org/index.html)
[![Chart.js Version](https://img.shields.io/badge/chart.js-latest-orange.svg)](https://www.chartjs.org/)

##  專案描述

本專案使用 Python 3.0 以上版本虛擬環境 `venv`，在樹莓派上建立一個動態伺服器，接收 ESP8266 收集的 DS18B20 溫度數據，並在前端網頁上呈現折線圖。

* **高效版**：使用循環緩衝表 (Circular Buffer Table)，不需要每次檢查並刪除舊數據，而是透過固定大小的表格和索引循環來自動覆蓋最舊的記錄，從而提升效率。

## ️ 專案架構

本專案架構包含以下幾個部分：

1.  **ESP8266 + DS18B20**：ESP8266 透過 OneWire 讀取 DS18B20 溫度數據，並透過 HTTP POST 傳送數據到樹莓派。
2.  **樹莓派 (Flask + SQLite)**：建立 Flask 伺服器，接收來自 ESP8266 的溫度數據，並存入 SQLite 資料庫。
3.  **前端 (HTML + Chart.js)**：使用 Chart.js 繪製折線圖，從 Flask API 獲取歷史溫度數據並呈現。

##  環境設定

* **樹莓派**：
    * SSH 登入使用者：`pi`
    * 密碼：`PASSWORD`
    * 請確保已安裝 Python 3.0 以上版本和 `venv`。
* **ESP8266**：
    * 請確保已安裝 Arduino IDE 和 ESP8266 開發板支援。
    * 請確保已安裝 OneWire 和 DallasTemperature 函式庫。

##  安裝步驟

1.  **在樹莓派上建立虛擬環境：**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **安裝 Flask 和其他必要的套件：**

    ```bash
    pip install flask
    ```

3.  **複製專案程式碼到樹莓派。**

4.  **在 ESP8266 上燒錄程式碼。**

5.  **啟動 Flask 伺服器：**

    ```bash
    python app.py
    ```

6.  **在瀏覽器中輸入樹莓派的 IP 位址和連接埠號 (預設為 5000) 即可查看即時溫度監控圖表。**

##  curl 模擬命令集

### 上傳溫度數據

```bash
curl -X POST -d "T1=25.6&T2=26.4&T3=25.3&T4=60.3" [http://192.168.2.90:5000/upload](http://192.168.2.90:5000/upload)
curl -X POST -d "T1=25.6&T2=26.4&T3=&T4=" [http://192.168.2.90:5000/upload](http://192.168.2.90:5000/upload)
curl -X POST -d "T1=25.6" [http://192.168.2.90:5000/upload](http://192.168.2.90:5000/upload)
curl -X POST -d "T2=25.6" [http://192.168.2.90:5000/upload](http://192.168.2.90:5000/upload)
curl -X POST -d "T3=25.6" [http://192.168.2.90:5000/upload](http://192.168.2.90:5000/upload)
curl -X POST -d "T4=25.6" [http://192.168.2.90:5000/upload](http://192.168.2.90:5000/upload)
