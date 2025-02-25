from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import pytz  # 處理時區
import time

app = Flask(__name__)

# 設定台灣時區
local_tz = pytz.timezone("Asia/Taipei")

# ✅ 等待時間同步（解決 Raspberry Pi 啟動時時間不準確問題）
def wait_for_time_sync():
    while True:
        current_time = datetime.now()
        if current_time.year > 2000:  # 檢查時間是否已同步
            print("✅ 時間同步成功:", current_time)
            break
        print("⏳ 等待時間同步...")
        time.sleep(5)

wait_for_time_sync()

# ✅ 初始化 SQLite 資料庫
def init_db():
    conn = sqlite3.connect("temperature.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ds18b20 REAL,           -- 用於儲存 T1 溫度數據
            lm35 REAL,              -- 用於儲存 T2 溫度數據
            dht11_temp REAL,        -- 用於儲存 T3 溫度數據
            dht11_humidity REAL,    -- 用於儲存 T4 濕度數據
            timestamp TEXT          -- 儲存數據的時間戳
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ✅ 接收 ESP8266/ESP32 傳來的數據（允許部分數據缺失）
@app.route("/upload", methods=["POST"])
def upload():
    try:
        # 獲取 POST 請求中的數據，若無值則為 None
        T1 = request.form.get("T1")  # 第一個溫度數據
        T2 = request.form.get("T2")  # 第二個溫度數據
        T3 = request.form.get("T3")  # 第三個溫度數據
        T4 = request.form.get("T4")  # 濕度數據

        # 至少需要一個數據才能存入資料庫
        if not (T1 or T2 or T3 or T4):
            return jsonify({"status": "error", "message": "No data provided"}), 400

        # 獲取當前台灣時間
        timestamp = datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        # 連接到資料庫
        conn = sqlite3.connect("temperature.db")
        cursor = conn.cursor()

        # 如果有最新數據，獲取前一筆記錄（用於保留未更新的值）
        cursor.execute("SELECT ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
        last_record = cursor.fetchone()
        
        # 如果有前一筆記錄，使用它作為預設值；否則設為 None
        if last_record:
            last_T1, last_T2, last_T3, last_T4 = last_record
        else:
            last_T1, last_T2, last_T3, last_T4 = None, None, None, None

        # 如果當前數據為空或無效，保留前一筆數據
        T1 = float(T1) if T1 else last_T1
        T2 = float(T2) if T2 else last_T2
        T3 = float(T3) if T3 else last_T3
        T4 = float(T4) if T4 else last_T4

        # 插入新數據到資料庫
        cursor.execute(
            "INSERT INTO sensor_data (ds18b20, lm35, dht11_temp, dht11_humidity, timestamp) VALUES (?, ?, ?, ?, ?)",
            (T1, T2, T3, T4, timestamp)
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": "Invalid data format"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ 提供 API，讓前端獲取 4 種數據
def get_filtered_data(range_type):
    conn = sqlite3.connect("temperature.db")
    cursor = conn.cursor()

    now = datetime.now(local_tz)
    
    if range_type == 'daily':
        start_time = now.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE timestamp >= ?", (start_time,))
    
    elif range_type == 'weekly':
        start_time = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE timestamp >= ?", (start_time,))
    
    elif range_type == 'monthly':
        start_time = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE timestamp >= ?", (start_time,))
    
    else:  # 'realTime' 預設返回最新 100 筆數據
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data ORDER BY timestamp DESC LIMIT 100")

    data = [{
        "timestamp": row[0],
        "T1": row[1],         # 原 ds18b20
        "T2": row[2],         # 原 lm35
        "T3": row[3],         # 原 dht11_temp
        "T4": row[4]          # 原 dht11_humidity
    } for row in cursor.fetchall()]
    
    conn.close()
    return data

@app.route("/data", methods=["GET"])
def get_data():
    range_type = request.args.get('range', 'realTime')
    data = get_filtered_data(range_type)
    return jsonify(data)

# ✅ 清除所有數據
@app.route("/clear", methods=["POST"])
def clear_data():
    conn = sqlite3.connect("temperature.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensor_data")
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "All data deleted"}), 200

# ✅ 提供前端網頁
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# ✅ 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
