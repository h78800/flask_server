from waitress import serve
from app import app  # 從 app.py 引入 Flask 實例

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
