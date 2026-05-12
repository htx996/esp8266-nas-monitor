FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

# psutil may need to compile native extensions on Alpine, so install build tools first.
RUN apk add --no-cache gcc python3-dev musl-dev linux-headers \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt \
    && apk del gcc python3-dev musl-dev linux-headers

COPY nas_status_server.py .

EXPOSE 8088

CMD ["python", "nas_status_server.py"]
