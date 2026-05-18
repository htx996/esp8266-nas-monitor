# ESP8266 NAS Monitor

<p align="center">
  <img src="custom_components/nas_monitoring_panel/icon.svg" alt="NAS Monitoring Panel" width="160">
</p>

基于 ESP8266 + ST7789 240x240 TFT 的 NAS 状态监控小屏项目。

## 功能

- 小屏显示 NAS 状态：CPU、内存、磁盘、CPU 温度、下载速度、上传速度、北京时间、日期
- NAS 端通过 Docker 部署 HTTP 状态接口
- ESP8266 支持 AP 配网页和 Web OTA
- Web 页面支持 Wi-Fi、NAS IP、端口、Token、刷新间隔、屏幕标题、Web 访问密码配置
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
├── custom_components/
│   └── nas_monitoring_panel/
│       ├── manifest.json
│       ├── icon.svg
│       └── ...
├── tft-espi/
│   └── User_Setup.h
├── docs/
│   └── tutorial.md
└── .github/workflows/docker-image.yml
```

## 快速开始

NAS 端提供两种部署方式，二选一即可，不要同时启动。

```text
方式 A：专用 Docker 镜像部署，推荐普通用户使用，不需要上传 Python 文件。
方式 B：源码目录部署，适合想自己修改 nas_status_server.py 的用户。
```

### 方式 A：专用 Docker 镜像部署，推荐

在 NAS 上创建目录：

```bash
mkdir -p /volume1/docker/esp8266-nas-status
cd /volume1/docker/esp8266-nas-status
```

创建 `docker-compose.yml`：

```yaml
services:
  nas-status:
    image: hanfu1997/esp8266-nas-status:latest
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

查看状态：

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

### 方式 B：源码目录部署

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

启动：

```bash
cd /volume1/docker/esp8266-nas-status
docker compose up -d
```

源码目录部署使用 `nas-server/docker-compose.yml`。

## 参数说明

`TOKEN` 是接口访问令牌，默认是：

```yaml
- TOKEN=abc123456
```

ESP8266 Web 配网页里的 Token 必须和 NAS 端一致。

`DISK_PATH` 是磁盘使用率统计路径，默认是：

```yaml
- DISK_PATH=/host
```

一般保持默认即可。

## 测试 NAS 接口

浏览器打开：

```text
http://NAS_IP:8088/status?token=abc123456
```

正常会返回：

```json
{"cpu":4,"disk":6,"down":"50KB/s","mem":65,"temp":54,"up":"73KB/s","uptime":365680}
```

## 配置 TFT_eSPI

用 `tft-espi/User_Setup.h` 替换 Arduino 库中的：

```text
TFT_eSPI/User_Setup.h
```

## 烧录 ESP8266 固件

打开：

```text
esp8266-firmware/esp8266_nas_monitor.ino
```

安装依赖库：

- TFT_eSPI
- ArduinoJson

然后编译上传。

## Web 配网

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
hanfu1997/esp8266-nas-status:latest
```

首次构建前，需要在 GitHub 仓库的 Actions Secrets 中配置 Docker Hub 用户名和 Docker Hub Access Token。

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
