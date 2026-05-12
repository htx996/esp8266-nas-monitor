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
│   ├── docker-compose.yml
│   ├── nas_status_server.py
│   └── requirements.txt
├── esp8266-firmware/
│   └── esp8266_nas_monitor.ino
├── tft-espi/
│   └── User_Setup.h
└── docs/
    └── tutorial.md
```

## 快速开始

### 1. 部署 NAS 端

NAS 端推荐使用 Docker Compose 部署。仓库已经提供好了完整的 Compose 配置文件：

```text
nas-server/docker-compose.yml
```

#### 方式 A：直接使用仓库里的 nas-server 目录

把 `nas-server` 目录上传到 NAS，例如：

```text
/volume1/docker/esp8266-nas-status
```

目录中应包含 3 个文件：

```text
esp8266-nas-status/
├── docker-compose.yml
├── nas_status_server.py
└── requirements.txt
```

进入目录：

```bash
cd /volume1/docker/esp8266-nas-status
```

启动服务：

```bash
docker compose up -d
```

查看容器状态：

```bash
docker compose ps
```

查看运行日志：

```bash
docker compose logs -f
```

停止服务：

```bash
docker compose down
```

重启服务：

```bash
docker compose restart
```

#### 方式 B：手动创建 docker-compose.yml

如果不想上传整个仓库，也可以在 NAS 上新建一个目录，然后手动创建 `docker-compose.yml`。

创建目录：

```bash
mkdir -p /volume1/docker/esp8266-nas-status
cd /volume1/docker/esp8266-nas-status
```

创建 `docker-compose.yml`：

```yaml
services:
  nas-status:
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.12-alpine
    container_name: esp8266-nas-status
    restart: unless-stopped
    network_mode: host
    working_dir: /app
    environment:
      - TOKEN=abc123456  //自定义设置//
      - DISK_PATH=/host
    volumes:
      - ./:/app
      - /:/host:ro
      - /sys:/sys:ro
    command: sh -c "pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt && python nas_status_server.py"
```

注意：如果使用方式 B，除了 `docker-compose.yml`，同目录下仍然需要放入：

```text
nas_status_server.py
requirements.txt
```

#### 可自定义参数

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

## 默认信息

- AP 热点：`NAS-Monitor-Setup`
- Web 用户名：`admin`
- 新设备默认无 Web 密码保护
- 设置 Web 访问密码后，后续进入 Web 页面需要登录
- 恢复出厂设置会清除 Web 密码保护

## 注意事项

- 屏幕左上角标题建议使用英文或数字，默认 TFT 字体不支持中文。
- 如果温度一直显示 27℃，通常是 NAS 端读取到了低温传感器，而不是 CPU Package 温度。本项目 NAS 端代码已优先读取 `Package id 0`。
- 如果屏幕微闪，可调整 ESP 固件中的 `analogWriteFreq()` 和 `analogWrite(LCD_BL_PIN, value)`。

## License

MIT
