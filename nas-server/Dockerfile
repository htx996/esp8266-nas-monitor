FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

COPY nas_status_server.py .

EXPOSE 8088

CMD ["python", "nas_status_server.py"]
