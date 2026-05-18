# homebridge-nas-monitoring-panel

实验性 Homebridge 插件，用于把 NAS Monitoring Panel 暴露到 Apple 家庭，尝试以 **电视 + 灯光亮度** 的组合形式显示。

## 功能

- Television 服务：用于屏幕开关
- Lightbulb 服务：用于屏幕亮度调节
- 通过 ESP HTTP 接口通信

依赖 ESP 固件接口：

```text
/api/display/on
/api/display/off
/api/display/status
/api/display/brightness?value=80
```

其中 `/api/display/status` 建议返回：

```json
{
  "power": true,
  "state": "on",
  "brightness": 80,
  "brightness_percent": 80,
  "schedule_enabled": true,
  "on_time": "08:00",
  "off_time": "23:00"
}
```

## 安装

先进入 Homebridge 所在机器的插件目录，或者任意工作目录：

```bash
git clone https://github.com/htx996/esp8266-nas-monitor.git
cd esp8266-nas-monitor/homebridge-nas-monitoring-panel
npm install -g .
```

如果你使用的是 Homebridge UI，也可以先把这个目录打包后本地安装。

## Homebridge 配置

在 `config.json` 中加入：

```json
{
  "platforms": [
    {
      "platform": "NasMonitoringPanel",
      "name": "NAS Monitoring Panel",
      "host": "192.168.2.115",
      "port": 80,
      "username": "admin",
      "password": "",
      "refreshSeconds": 15,
      "https": false
    }
  ]
}
```

### 参数说明

- `platform`: 固定为 `NasMonitoringPanel`
- `name`: 在 Apple 家庭中显示的名称
- `host`: ESP 设备 IP
- `port`: ESP Web 端口，默认 80
- `username`: Web 用户名，默认 `admin`
- `password`: Web 密码；如果 ESP 没启用 Web 密码保护可留空
- `refreshSeconds`: 轮询刷新秒数，默认建议 15
- `https`: 是否使用 HTTPS，通常为 `false`

## 预期效果

Apple 家庭里会尝试出现一个桥接设备，其中包含：

- 电视控制：开/关屏幕
- 灯光控制：调节亮度

是否最终显示为一个合并配件，还是两个分开的可视项，取决于 Apple 家庭对该组合服务的呈现方式。

## 注意事项

- 这是实验性方案，优先用于测试是否能达到你想要的 HomeKit 展现效果。
- 如果 Homebridge 中电视与灯光仍被拆分显示，这是 HomeKit 客户端的显示行为，不一定是插件错误。
- 如果亮度无效，先确认 ESP 固件已经刷入带 brightness API 的版本。
- 如果认证失败，请确认 ESP Web 用户名密码是否与配置一致。
