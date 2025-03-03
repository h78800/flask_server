from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import pytz  # 處理時區
import time

app = Flask(__name__)

# 設定台灣時區
local_tz = pytz.timezone("Asia/Taipei")

# ✅ 設定循環緩衝表的最大筆數(測試時可以修改為10或100)
MAX_RECORDS = 40000

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

# ✅ 初始化 SQLite 資料庫（使用循環緩衝表）
def init_db():
    conn = sqlite3.connect("temperature.db")
    cursor = conn.cursor()
    
    # 創建主數據表（固定大小）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY,  -- 範圍從 0 到 MAX_RECORDS-1
            ds18b20 REAL,            -- 用於儲存 T1 溫度數據
            lm35 REAL,               -- 用於儲存 T2 溫度數據
            dht11_temp REAL,         -- 用於儲存 T3 溫度數據
            dht11_humidity REAL,     -- 用於儲存 T4 濕度數據
            timestamp TEXT           -- 儲存數據的時間戳
        )
    """)
    
    # 創建索引追蹤表（儲存當前寫入位置）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buffer_info (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    
    # 初始化索引（若不存在則設為 0）
    cursor.execute("INSERT OR IGNORE INTO buffer_info (key, value) VALUES ('current_index', 0)")
    
    # 預填充表格（確保有 MAX_RECORDS 筆記錄）
    cursor.execute("SELECT COUNT(*) FROM sensor_data")
    current_count = cursor.fetchone()[0]
    if current_count < MAX_RECORDS:
        for i in range(current_count, MAX_RECORDS):
            cursor.execute(
                "INSERT INTO sensor_data (id, ds18b20, lm35, dht11_temp, dht11_humidity, timestamp) VALUES (?, NULL, NULL, NULL, NULL, NULL)",
                (i,)
            )
    
    conn.commit()
    conn.close()

init_db()

# ✅ 接收 ESP8266/ESP32 傳來的數據（使用循環緩衝表）
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

        # 獲取當前索引
        cursor.execute("SELECT value FROM buffer_info WHERE key = 'current_index'")
        current_index = cursor.fetchone()[0]

        # 如果有最新數據，獲取前一筆記錄（用於保留未更新的值）
        prev_index = (current_index - 1) % MAX_RECORDS
        cursor.execute("SELECT ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE id = ?", (prev_index,))
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

        # 更新當前索引位置的數據（覆蓋舊數據）
        cursor.execute(
            "UPDATE sensor_data SET ds18b20 = ?, lm35 = ?, dht11_temp = ?, dht11_humidity = ?, timestamp = ? WHERE id = ?",
            (T1, T2, T3, T4, timestamp, current_index)
        )

        # 更新索引（循環回到 0）
        next_index = (current_index + 1) % MAX_RECORDS
        cursor.execute("UPDATE buffer_info SET value = ? WHERE key = 'current_index'", (next_index,))
        
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

    # 獲取當前索引
    cursor.execute("SELECT value FROM buffer_info WHERE key = 'current_index'")
    current_index = cursor.fetchone()[0]

    now = datetime.now(local_tz)
    
    if range_type == 'daily':
        start_time = now.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE timestamp >= ? AND timestamp IS NOT NULL ORDER BY timestamp", (start_time,))
    
    elif range_type == 'weekly':
        start_time = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE timestamp >= ? AND timestamp IS NOT NULL ORDER BY timestamp", (start_time,))
    
    elif range_type == 'monthly':
        start_time = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE timestamp >= ? AND timestamp IS NOT NULL ORDER BY timestamp", (start_time,))
    
    else:  # 'realTime' 預設返回最新 100 筆數據
        # 從 current_index 往前取 100 筆
        start_id = max(0, current_index - 100)
        cursor.execute("SELECT timestamp, ds18b20, lm35, dht11_temp, dht11_humidity FROM sensor_data WHERE id >= ? AND id < ? AND timestamp IS NOT NULL ORDER BY id", (start_id, current_index))

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

# ✅ 清除所有數據（重置循環緩衝表）
@app.route("/clear", methods=["POST"])
def clear_data():
    conn = sqlite3.connect("temperature.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE sensor_data SET ds18b20 = NULL, lm35 = NULL, dht11_temp = NULL, dht11_humidity = NULL, timestamp = NULL")
    cursor.execute("UPDATE buffer_info SET value = 0 WHERE key = 'current_index'")
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "All data reset"}), 200

# ✅ 提供前端網頁
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# ✅ 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)