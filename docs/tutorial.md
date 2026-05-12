# ESP8266 NAS Monitor 零基础部署教程

本教程面向零基础用户，说明如何从零部署 NAS 端服务、配置 TFT_eSPI、烧录 ESP8266 固件，并完成 Web 配网。

## 1. 项目由哪些部分组成

本项目分为三部分：

```text
1. NAS 端服务
2. ESP8266 固件
3. TFT_eSPI 屏幕库配置
```

仓库目录：

```text
esp8266-nas-monitor/
├── nas-server/
│   ├── docker-compose.yml
│   ├── nas_status_server.py
│   └── requirements.txt
├── esp8266-firmware/
│   └── esp8266_nas_monitor.ino
├── tft-espi/
│   └── User_Setup.h
└── README.md
```

## 2. NAS 端 3 个文件分别做什么

### docker-compose.yml

用于启动 Docker 容器。它负责：

- 使用 Python 3.12 Alpine 镜像
- 安装 Python 依赖
- 启动 `nas_status_server.py`
- 设置接口 Token
- 挂载 NAS 系统目录用于读取磁盘和温度信息

默认 Token：

```yaml
- TOKEN=abc123456
```

你可以改成自己的，例如：

```yaml
- TOKEN=mytoken123
```

ESP8266 Web 配网页里的 Token 必须和这里一致。

### nas_status_server.py

这是 NAS 状态接口服务，负责读取：

- CPU 使用率
- 内存使用率
- 磁盘使用率
- CPU 温度
- 上传速度
- 下载速度
- 系统运行时间

接口地址示例：

```text
http://NAS_IP:8088/status?token=abc123456
```

返回示例：

```json
{
  "cpu": 4,
  "disk": 6,
  "down": "50KB/s",
  "mem": 65,
  "temp": 54,
  "up": "73KB/s",
  "uptime": 365680
}
```

ESP8266 就是读取这个 JSON，然后显示到屏幕上。

### requirements.txt

Python 依赖列表：

```text
flask
psutil
```

其中：

- `flask` 用来提供 HTTP 接口
- `psutil` 用来读取 NAS 系统状态

## 3. 部署 NAS 端

### 3.1 上传 nas-server 目录

把仓库里的 `nas-server` 文件夹上传到 NAS，例如：

```text
/volume1/docker/esp8266-nas-status
```

如果你的 NAS 路径不同，可以自行调整。

### 3.2 修改 Token

打开：

```text
nas-server/docker-compose.yml
```

找到：

```yaml
- TOKEN=abc123456
```

可以保持默认，也可以改成自己的 Token。

### 3.3 启动服务

进入 NAS SSH 终端，执行：

```bash
cd /volume1/docker/esp8266-nas-status
docker compose up -d
```

### 3.4 测试接口

浏览器打开：

```text
http://你的NAS_IP:8088/status?token=abc123456
```

例如：

```text
http://192.168.2.86:8088/status?token=abc123456
```

如果看到 JSON 数据，说明 NAS 端成功。

## 4. 配置 TFT_eSPI

Arduino 使用 TFT_eSPI 驱动 ST7789 屏幕。必须先替换库文件中的 `User_Setup.h`。

### 4.1 找到 TFT_eSPI/User_Setup.h

Arduino 库目录通常在：

```text
Documents/Arduino/libraries/TFT_eSPI/User_Setup.h
```

### 4.2 替换文件

用仓库中的：

```text
tft-espi/User_Setup.h
```

替换 Arduino 库中的：

```text
TFT_eSPI/User_Setup.h
```

本项目屏幕接线：

```text
SCK  -> GPIO14
MOSI -> GPIO13
DC   -> GPIO0
RST  -> GPIO2
BL   -> GPIO5，低电平点亮
CS   -> GND
```

## 5. 烧录 ESP8266 固件

### 5.1 安装 Arduino 库

Arduino IDE 里安装：

- TFT_eSPI
- ArduinoJson

### 5.2 打开固件

打开：

```text
esp8266-firmware/esp8266_nas_monitor.ino
```

选择你的 ESP8266 开发板，然后上传。

## 6. 首次配网

首次启动时，如果没有保存 Wi-Fi，设备会开启 AP 热点：

```text
NAS-Monitor-Setup
```

手机连接这个热点后，通常会自动弹出配置页。

如果没有自动弹出，手动打开：

```text
http://192.168.4.1
```

需要填写：

- 屏幕左上角名称
- Wi-Fi SSID
- Wi-Fi 密码
- NAS IP
- NAS 端口
- Token
- 刷新间隔
- Web 访问密码，可选

示例：

```text
屏幕左上角名称：UGREEN NAS
Wi-Fi SSID：你的 Wi-Fi 名称
Wi-Fi 密码：你的 Wi-Fi 密码
NAS IP：192.168.2.86
NAS 端口：8088
Token：abc123456
刷新间隔：3
```

保存后设备会重启并连接 Wi-Fi。

## 7. 联网逻辑

设备启动后：

1. 优先连接上次保存的 Wi-Fi。
2. 连接失败会继续重试。
3. 一段时间后自动开启 AP 配网热点。
4. AP 开启后，仍会继续尝试连接上次保存的 Wi-Fi。
5. Wi-Fi 连接成功后，关闭 AP，进入正常监控界面。

## 8. Web 页面功能

进入设备 IP，例如：

```text
http://ESP_IP
```

页面支持：

- 修改 Wi-Fi
- 修改 NAS IP / 端口 / Token
- 修改刷新间隔
- 修改屏幕左上角名称
- 设置 Web 访问密码
- Web OTA 上传固件
- 清除 Wi-Fi 信息
- 开启 AP
- 重启设备
- 恢复出厂设置

## 9. Web OTA 固件升级

打开：

```text
http://ESP_IP/update
```

选择 Arduino IDE 导出的 `.bin` 固件并上传。

上传过程中：

- Web 页面显示进度条
- ESP 屏幕显示 OTA 进度
- 上传完成后自动重启

## 10. 屏幕标题注意事项

屏幕左上角名称建议使用英文、数字，例如：

```text
UGREEN NAS
HOME NAS
NAS-01
```

不建议使用中文，因为默认 TFT 字体通常不支持中文。

## 11. 温度一直显示 27℃怎么办

如果 Web 接口返回：

```json
"temp": 27
```

说明 NAS 端读取到的是低温传感器，不是 CPU Package 温度。

本项目 `nas_status_server.py` 已经优先读取：

```text
Package id 0
```

你可以在 NAS 终端执行下面命令检查传感器：

```bash
for f in /sys/class/hwmon/hwmon*/temp*_input; do
  echo "$f"
  cat "${f%_input}_label" 2>/dev/null
  cat "$f" 2>/dev/null
  echo
done
```

如果看到：

```text
Package id 0
63000
```

表示 CPU Package 温度是 63℃。

## 12. 背光亮度和微闪

ESP 固件中这几行控制背光：

```cpp
analogWriteRange(1023);
analogWriteFreq(10000);
analogWrite(LCD_BL_PIN, 600);
```

因为本项目背光是低电平点亮：

```text
数值越小越亮
数值越大越暗
```

例如：

```text
300 较亮
600 中等
900 较暗
```

如果屏幕微闪，可以尝试修改频率：

```cpp
analogWriteFreq(5000);
```

或者：

```cpp
analogWriteFreq(1000);
```

## 13. 恢复出厂设置

Web 页面点击“恢复出厂设置”后会清除：

- Wi-Fi 信息
- NAS 配置
- Token
- Web 访问密码
- 屏幕标题

设备重启后会重新进入 AP 配网模式。
