#include <ESP8266WiFi.h>    // ESP8266 的 Wi-Fi 函式庫
#include <ESP8266HTTPClient.h> // 用於發送 HTTP 請求
#include <WiFiClient.h>     // 提供 Wi-Fi 客戶端功能
#include <OneWire.h>        // OneWire 通訊協議
#include <DallasTemperature.h> // DS18B20 溫度感測器函式庫
#include <EEPROM.h>         // EEPROM 函式庫，用於持久化儲存
#include <WiFiManager.h>    // WiFiManager 函式庫，用於動態配置 Wi-Fi

// ✅ 伺服器設定（初始值，可被使用者覆蓋）
String serverName = "http://192.168.0.246:5000/upload"; // 預設 Flask 伺服器上傳端點

// ✅ 定義引腳（根據您的硬體連接修改）
#define ONE_WIRE_BUS1 D1  // T1 感測器引腳
#define ONE_WIRE_BUS2 D2  // T2 感測器引腳
#define ONE_WIRE_BUS3 D3  // T3 感測器引腳
#define ONE_WIRE_BUS4 D4  // T4 感測器引腳

// ✅ EEPROM 設定
#define EEPROM_SIZE 512   // EEPROM 分配大小（ESP8266 最多 4096 位元組）
#define SERVER_ADDR 0     // serverName 儲存起始地址

// ✅ 自訂 AP 名稱
const char* customAPName = "SensorHub"; // 自訂 AP 名稱，可自行修改

// ✅ 初始化 OneWire 和 DallasTemperature 物件
OneWire oneWire1(ONE_WIRE_BUS1);
OneWire oneWire2(ONE_WIRE_BUS2);
OneWire oneWire3(ONE_WIRE_BUS3);
OneWire oneWire4(ONE_WIRE_BUS4);
DallasTemperature sensor1(&oneWire1);
DallasTemperature sensor2(&oneWire2);
DallasTemperature sensor3(&oneWire3);
DallasTemperature sensor4(&oneWire4);

// ✅ 從 EEPROM 讀取 serverName
void loadServerName() {
  EEPROM.begin(EEPROM_SIZE);
  String loaded = "";
  for (int i = SERVER_ADDR; i < EEPROM_SIZE; i++) {
    char c = EEPROM.read(i);
    if (c == 0 || c == '\n') break; // 遇到結束符號停止
    loaded += c;
  }
  if (loaded.length() > 0) {
    serverName = loaded; // 如果 EEPROM 有值，覆蓋預設值
  }
  EEPROM.end();
}

// ✅ 將 serverName 儲存到 EEPROM
void saveServerName(String url) {
  EEPROM.begin(EEPROM_SIZE);
  for (int i = 0; i < url.length(); i++) {
    EEPROM.write(SERVER_ADDR + i, url[i]);
  }
  EEPROM.write(SERVER_ADDR + url.length(), 0); // 添加結束符號
  EEPROM.commit(); // 提交更改
  EEPROM.end();
}

// ✅ WiFiManager 配置保存回調（舊版）
void configModeCallback(WiFiManager *myWiFiManager) {
  Serial.println("進入配置模式");
  Serial.print("請連接到 AP: ");
  Serial.println(customAPName);
  Serial.print("IP 地址: ");
  Serial.println(WiFi.softAPIP());
}

// ✅ 設置函數：初始化 ESP8266 和感測器
void setup() {
  Serial.begin(115200); // 啟動序列埠，波特率設為 115200
  delay(1000);          // 等待 1 秒，讓序列埠穩定

  // ✅ 從 EEPROM 載入先前的 serverName
  loadServerName();
  Serial.println("從 EEPROM 載入的伺服器 URL: " + serverName);

  // ✅ 初始化 WiFiManager
  WiFiManager wifiManager;
  // wifiManager.resetSettings(); // 可取消註解以重置已儲存的 Wi-Fi 設定

  // ✅ 新增自訂參數：伺服器 URL
  char serverNameBuffer[100]; // 緩衝區，用於儲存 URL
  serverName.toCharArray(serverNameBuffer, 100); // 將 String 轉為 char 陣列
  WiFiManagerParameter customServerName("server", "伺服器 URL", serverNameBuffer, 100); // 自訂輸入欄位

  wifiManager.addParameter(&customServerName); // 將自訂參數加入配置頁面
  wifiManager.setAPCallback(configModeCallback); // 設置配置模式回調

  Serial.println("正在啟動 WiFi 配置模式...");
  if (!wifiManager.autoConnect(customAPName)) { // 使用自訂 AP 名稱
    Serial.println("WiFi 連接失敗，重啟中...");
    ESP.restart(); // 如果連接失敗，重啟
  }

  // ✅ 獲取並保存用戶輸入的伺服器 URL
  String newServerName = customServerName.getValue();
  if (newServerName.length() > 0 && newServerName != serverName) {
    serverName = newServerName;
    saveServerName(serverName); // 如果有新值，儲存到 EEPROM
    Serial.println("已更新並儲存伺服器 URL（配置頁面）: " + serverName);
  }

  Serial.println("WiFi 已連接");
  Serial.print("ESP8266 IP 地址: ");
  Serial.println(WiFi.localIP()); // 顯示 ESP8266 的 IP 地址
  Serial.println("使用中的伺服器 URL: " + serverName);

  // ✅ 自訂伺服器 URL（備用，通過序列埠）
  Serial.println("如需修改伺服器 URL，請在 10 秒內輸入新值（例如 http://192.168.1.100:8080/data），或留空使用當前值：");
  unsigned long startTime = millis();
  const unsigned long timeout = 10000; // 10 秒超時
  String input = "";
  
  while (millis() - startTime < timeout && !Serial.available()) {
    delay(100); // 等待使用者輸入或超時
  }
  
  if (Serial.available()) {
    input = Serial.readStringUntil('\n'); // 讀取使用者輸入
    input.trim(); // 移除前後空白
    if (input.length() > 0) { // 如果有輸入，則更新並儲存
      serverName = input;
      saveServerName(serverName);
      Serial.println("已更新並儲存伺服器 URL（序列埠）: " + serverName);
    } else {
      Serial.println("未輸入新值，使用當前伺服器 URL: " + serverName);
    }
  } else {
    Serial.println("超時，未輸入新值，使用當前伺服器 URL: " + serverName);
  }

  // 初始化 DS18B20 感測器
  sensor1.begin();
  sensor2.begin();
  sensor3.begin();
  sensor4.begin();
}

// ✅ 主循環函數：讀取真實感測器數據並上傳
void loop() {
  if (WiFi.status() == WL_CONNECTED) { // 確認 Wi-Fi 是否仍連接
    WiFiClient client;       // 創建 Wi-Fi 客戶端物件
    HTTPClient http;         // 創建 HTTPClient 物件

    // ✅ 從 DS18B20 感測器讀取溫度
    sensor1.requestTemperatures();
    sensor2.requestTemperatures();
    sensor3.requestTemperatures();
    sensor4.requestTemperatures();
    
    float T1 = sensor1.getTempCByIndex(0); // 讀取 T1 溫度 (°C)
    float T2 = sensor2.getTempCByIndex(0); // 讀取 T2 溫度 (°C)
    float T3 = sensor3.getTempCByIndex(0); // 讀取 T3 溫度 (°C)
    float T4 = sensor4.getTempCByIndex(0); // 讀取 T4 溫度 (°C)

    // ✅ 檢查是否讀取失敗
    if (T1 == DEVICE_DISCONNECTED_C) T1 = -127; // 感測器未連接時設為 -127
    if (T2 == DEVICE_DISCONNECTED_C) T2 = -127;
    if (T3 == DEVICE_DISCONNECTED_C) T3 = -127;
    if (T4 == DEVICE_DISCONNECTED_C) T4 = -127;

    // ✅ 顯示數據到序列埠
    Serial.println("感測器數據:");
    Serial.print("T1 = "); Serial.print(T1); Serial.println(" °C");
    Serial.print("T2 = "); Serial.print(T2); Serial.println(" °C");
    Serial.print("T3 = "); Serial.print(T3); Serial.println(" °C");
    Serial.print("T4 = "); Serial.print(T4); Serial.println(" °C");

    // ✅ 準備 POST 請求的數據
    String postData = "T1=" + String(T1) + "&T2=" + String(T2) + "&T3=" + String(T3) + "&T4=" + String(T4);

    // ✅ 發送 HTTP POST 請求
    http.begin(client, serverName); // 使用自訂的 serverName
    http.addHeader("Content-Type", "application/x-www-form-urlencoded"); // 設定表單數據格式

    int httpResponseCode = http.POST(postData); // 發送 POST 請求並獲取回應碼

    // ✅ 檢查回應
    if (httpResponseCode > 0) { // 如果回應碼大於 0，表示成功收到回應
      String response = http.getString(); // 獲取伺服器回應內容
      Serial.print("HTTP 回應碼: ");
      Serial.println(httpResponseCode); // 顯示回應碼（200 表示成功）
      Serial.print("伺服器回應: ");
      Serial.println(response); // 顯示伺服器回應
    } else {
      Serial.print("錯誤碼: ");
      Serial.println(httpResponseCode); // 顯示錯誤碼
    }

    http.end(); // 結束 HTTP 連線
  } else {
    Serial.println("WiFi 連接中斷"); // 如果 Wi-Fi 斷線，顯示提示
  }

  delay(10000); // 每 10 秒上傳一次數據（可調整）
}
