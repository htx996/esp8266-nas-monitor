# ESP8266 NAS Monitor

基于 ESP8266 + ST7789 240x240 TFT 的 NAS 状态监控小屏项目。

## 功能

- 小屏显示 NAS 状态：CPU、内存、磁盘、CPU 温度、下载速度、上传速度、北京时间、日期
- NAS 端通过 Docker 部署 HTTP 状态接口
- ESP8266 支持 AP 配网页
- 手机连接热点后可进入 Web 配置页
- 支持 Wi-Fi、NAS IP、端口、Token、刷新间隔、屏幕标题、Web 访问密码配置
- 支持 Web OTA 上传固件
- 支持清除 Wi-Fi 信息、开启 AP、重启设备、恢复出厂设置

## 仓库结构

```text
esp8266-nas-monitor/
├── README.md
├── LICENSE
├── nas-server/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.image.yml
│   ├── nas_status_server.py
│   └── requirements.txt
├── esp8266-firmware/
│   └── esp8266_nas_monitor.ino
├── tft-espi/
│   └── User_Setup.h
├── docs/
│   └── tutorial.md
└── .github/
    └── workflows/
        └── docker-image.yml
```

## 快速开始

### 1. 部署 NAS 端

NAS 端提供两种部署方式，二选一即可，不要同时启动。

```text
方式 A：专用 Docker 镜像部署，推荐普通用户使用，不需要上传 Python 文件。
方式 B：源码目录部署，适合想自己修改 nas_status_server.py 的用户。
```

#### 方式 A：专用 Docker 镜像部署，推荐

这种方式只需要一个 `docker-compose.yml`，不需要上传 `nas_status_server.py` 和 `requirements.txt`。

在 NAS 上创建目录：

```bash
mkdir -p /volume1/docker/esp8266-nas-status
cd /volume1/docker/esp8266-nas-status
```

创建 `docker-compose.yml`，内容如下：

```yaml
services:
  nas-status:
    image: htx996/esp8266-nas-status:latest
    container_name: esp8266-nas-status
    restart: unless-stopped
    network_mode: host
    environment:
      - TOKEN=abc123456
      - DISK_PATH=/host
    volumes:
      - /:/host:ro
      - /sys:/sys:ro
```

启动服务：

```bash
docker compose up -d
```

如果你的 NAS 使用旧版 Docker Compose，命令可能是：

```bash
docker-compose up -d
```

查看容器状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f
```

停止服务：

```bash
docker compose down
```

#### 方式 B：源码目录部署，保留原方法

把 `nas-server` 目录上传到 NAS，例如：

```text
/volume1/docker/esp8266-nas-status
```

目录中应包含：

```text
esp8266-nas-status/
├── docker-compose.yml
├── nas_status_server.py
└── requirements.txt
```

进入目录并启动：

```bash
cd /volume1/docker/esp8266-nas-status
docker compose up -d
```

源码目录部署使用的 `docker-compose.yml` 是：

```yaml
services:
  nas-status:
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.12-alpine
    container_name: esp8266-nas-status
    restart: unless-stopped
    network_mode: host
    working_dir: /app
    environment:
      - TOKEN=abc123456
      - DISK_PATH=/host
    volumes:
      - ./:/app
      - /:/host:ro
      - /sys:/sys:ro
    command: sh -c "pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt && python nas_status_server.py"
```

#### 参数说明

`TOKEN` 是接口访问令牌，默认是：

```yaml
- TOKEN=abc123456
```

你可以改成自己的，例如：

```yaml
- TOKEN=mytoken123
```

ESP8266 Web 配网页里的 Token 必须和这里保持一致。

`DISK_PATH` 是磁盘使用率统计路径，默认是：

```yaml
- DISK_PATH=/host
```

一般保持默认即可。

#### 浏览器测试 NAS 接口

浏览器打开：

```text
http://NAS_IP:8088/status?token=abc123456
```

例如：

```text
http://192.168.2.86:8088/status?token=abc123456
```

正常会返回：

```json
{"cpu":4,"disk":6,"down":"50KB/s","mem":65,"temp":54,"up":"73KB/s","uptime":365680}
```

### 2. 配置 TFT_eSPI

用 `tft-espi/User_Setup.h` 替换 Arduino 库中的：

```text
TFT_eSPI/User_Setup.h
```

### 3. 烧录 ESP8266 固件

打开：

```text
esp8266-firmware/esp8266_nas_monitor.ino
```

安装依赖库：

- TFT_eSPI
- ArduinoJson

然后编译上传。

### 4. Web 配网

首次启动或 Wi-Fi 连接失败后，ESP8266 会开启热点：

```text
NAS-Monitor-Setup
```

手机连接后打开：

```text
http://192.168.4.1
```

填写 NAS IP、端口、Token 后保存重启。

## Docker 镜像维护说明

专用镜像由 GitHub Actions 自动构建，工作流文件为：

```text
.github/workflows/docker-image.yml
```

镜像名：

```text
htx996/esp8266-nas-status:latest
```

如果你修改了 `nas-server/` 目录下的代码，GitHub Actions 会自动构建并推送新镜像。首次使用前需要在 GitHub 仓库 Secrets 中配置：

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

其中 `DOCKERHUB_TOKEN` 是 Docker Hub 里创建的 Access Token。

## 默认信息

- AP 热点：`NAS-Monitor-Setup`
- Web 用户名：`admin`
- 新设备默认无 Web 密码保护
- 设置 Web 访问密码后，后续进入 Web 页面需要登录
- 恢复出厂设置会清除 Web 密码保护

## 注意事项

- 两种 NAS 端部署方式二选一，不要同时启动。
- 屏幕左上角标题建议使用英文或数字，默认 TFT 字体不支持中文。
- 如果温度一直显示 27℃，通常是 NAS 端读取到了低温传感器，而不是 CPU Package 温度。本项目 NAS 端代码已优先读取 `Package id 0`。
- 如果屏幕微闪，可调整 ESP 固件中的 `analogWriteFreq()` 和 `analogWrite(LCD_BL_PIN, value)`。

## License

MIT
