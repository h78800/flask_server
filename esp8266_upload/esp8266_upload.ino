/*
2025/03/05 
4ch_upload_demo
模擬數據上傳
*/
#include <ESP8266WiFi.h>    // ESP8266 的 Wi-Fi 函式庫
#include <ESP8266HTTPClient.h> // 用於發送 HTTP 請求
#include <WiFiClient.h>     // 提供 Wi-Fi 客戶端功能

// ✅ Wi-Fi 設定
const char* ssid = "HomeAssistant1";      // 替換為您的 Wi-Fi 名稱
const char* password = "25693927";  // 替換為您的 Wi-Fi 密碼

// ✅ 伺服器設定
const char* serverName = "http://192.168.2.128:5000/upload"; // 替換為您的Flask 伺服器的上傳端點

// ✅ 定義模擬數據範圍
const float T1_MIN = 20.0;  // T1 溫度最小值 (°C)
const float T1_MAX = 30.0;  // T1 溫度最大值 (°C)
const float T2_MIN = 22.0;  // T2 溫度最小值 (°C)
const float T2_MAX = 32.0;  // T2 溫度最大值 (°C)
const float T3_MIN = 24.0;  // T3 溫度最小值 (°C)
const float T3_MAX = 34.0;  // T3 溫度最大值 (°C)
const float T4_MIN = 40.0;  // T4 濕度最小值 (%)
const float T4_MAX = 60.0;  // T4 濕度最大值 (%)

// ✅ 設置函數：初始化 ESP8266
void setup() {
  Serial.begin(115200); // 啟動序列埠，波特率設為 115200
  delay(1000);          // 等待 1 秒，讓序列埠穩定

  // ✅ 連接到 Wi-Fi
  Serial.println("正在連接到 WiFi...");
  WiFi.begin(ssid, password); // 開始連接到指定的 Wi-Fi

  while (WiFi.status() != WL_CONNECTED) { // 等待 Wi-Fi 連接成功
    delay(500);
    Serial.print("."); // 每 0.5 秒印一個點，表示正在連接
  }
  
  Serial.println("");
  Serial.println("WiFi 已連接");
  Serial.print("ESP8266 IP 地址: ");
  Serial.println(WiFi.localIP()); // 顯示 ESP8266 的 IP 地址
}

// ✅ 主循環函數：模擬數據並上傳
void loop() {
  if (WiFi.status() == WL_CONNECTED) { // 確認 Wi-Fi 是否仍連接
    WiFiClient client;       // 創建 Wi-Fi 客戶端物件
    HTTPClient http;         // 創建 HTTPClient 物件

    // ✅ 生成亂數模擬數據
    float T1 = random(T1_MIN * 10, T1_MAX * 10) / 10.0; // 生成 T1 亂數（保留一位小數）
    float T2 = random(T2_MIN * 10, T2_MAX * 10) / 10.0; // 生成 T2 亂數
    float T3 = random(T3_MIN * 10, T3_MAX * 10) / 10.0; // 生成 T3 亂數
    float T4 = random(T4_MIN * 10, T4_MAX * 10) / 10.0; // 生成 T4 亂數

    // ✅ 顯示生成的數據到序列埠
    Serial.println("模擬數據:");
    Serial.print("T1 = "); Serial.print(T1); Serial.println(" °C");
    Serial.print("T2 = "); Serial.print(T2); Serial.println(" °C");
    Serial.print("T3 = "); Serial.print(T3); Serial.println(" °C");
    Serial.print("T4 = "); Serial.print(T4); Serial.println(" %");

    // ✅ 準備 POST 請求的數據
    String postData = "T1=" + String(T1) + "&T2=" + String(T2) + "&T3=" + String(T3) + "&T4=" + String(T4);

    // ✅ 發送 HTTP POST 請求
    http.begin(client, serverName); // 初始化 HTTP 連線到伺服器（ESP8266 需要 WiFiClient）
    http.addHeader("Content-Type", "application/x-www-form-urlencoded"); // 設定表單數據格式

    int httpResponseCode = http.POST(postData); // 發送 POST 請求並獲取回應碼

    // ✅ 檢查回應
    if (httpResponseCode > 0) { // 如果回應碼大於 0，表示成功收到回應
      String response = http.getString(); // 獲取伺服器回應內容
      Serial.print("HTTP 回應碼: ");
      Serial.println(httpResponseCode); // 顯示回應碼（200 表示成功）
      Serial.print("伺服器回應: ");
      Serial.println(response); // 顯示伺服器回應（如 {"status": "success"}）
    } else {
      Serial.print("錯誤碼: ");
      Serial.println(httpResponseCode); // 顯示錯誤碼（負數表示連接失敗）
    }

    http.end(); // 結束 HTTP 連線
  } else {
    Serial.println("WiFi 連接中斷"); // 如果 Wi-Fi 斷線，顯示提示
  }

  delay(10000); // 每 10 秒上傳一次數據（可調整）
}

// ✅ 自訂函數：生成浮點亂數（未直接使用，但保留供參考）
float randomFloat(float min, float max) {
  return min + (float)random(0, 1000) / 1000.0 * (max - min); // 生成範圍內的浮點數
}
