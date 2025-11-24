# 使用官方 Python 3.11 作為 base image
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製整個專案到容器內
COPY . .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 設定容器啟動指令
CMD ["python", "main.py"]

