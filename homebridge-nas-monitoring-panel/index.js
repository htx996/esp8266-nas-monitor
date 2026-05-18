const http = require('http');
const https = require('https');
const { URL } = require('url');

const PLUGIN_NAME = 'homebridge-nas-monitoring-panel';
const PLATFORM_NAME = 'NasMonitoringPanel';

module.exports = (api) => {
  api.registerPlatform(PLUGIN_NAME, PLATFORM_NAME, NasMonitoringPanelPlatform);
};

class NasMonitoringPanelPlatform {
  constructor(log, config, api) {
    this.log = log;
    this.config = config || {};
    this.api = api;
    this.Service = api.hap.Service;
    this.Characteristic = api.hap.Characteristic;
    this.accessories = [];

    api.on('didFinishLaunching', () => {
      this.setupAccessory();
    });
  }

  configureAccessory(accessory) {
    this.accessories.push(accessory);
  }

  setupAccessory() {
    const host = this.config.host;
    const port = Number(this.config.port || 80);
    const username = this.config.username || 'admin';
    const password = this.config.password || '';
    const name = this.config.name || 'NAS Monitoring Panel';

    if (!host) {
      this.log.error('Missing host in Homebridge config for NAS Monitoring Panel');
      return;
    }

    const uuid = this.api.hap.uuid.generate(`nas-monitoring-panel:${host}:${port}`);
    let accessory = this.accessories.find((item) => item.UUID === uuid);

    if (!accessory) {
      accessory = new this.api.platformAccessory(name, uuid);
      this.api.registerPlatformAccessories(PLUGIN_NAME, PLATFORM_NAME, [accessory]);
    }

    const client = new PanelClient({ host, port, username, password, log: this.log, https: !!this.config.https });

    accessory.getService(this.Service.AccessoryInformation)
      .setCharacteristic(this.Characteristic.Manufacturer, 'htx996')
      .setCharacteristic(this.Characteristic.Model, 'NAS Monitoring Panel')
      .setCharacteristic(this.Characteristic.SerialNumber, `${host}:${port}`)
      .setCharacteristic(this.Characteristic.FirmwareRevision, '0.1.0');

    const tv = accessory.getService(this.Service.Television) || accessory.addService(this.Service.Television, name, 'tv');
    tv.setCharacteristic(this.Characteristic.ConfiguredName, name);
    tv.setCharacteristic(this.Characteristic.SleepDiscoveryMode, this.Characteristic.SleepDiscoveryMode.ALWAYS_DISCOVERABLE);
    tv.setPrimaryService(true);

    const light = accessory.getService(this.Service.Lightbulb) || accessory.addService(this.Service.Lightbulb, `${name} Light`, 'light');

    const state = {
      power: false,
      brightness: 100,
    };

    const refresh = async () => {
      try {
        const data = await client.status();
        state.power = normalizePower(data);
        state.brightness = normalizeBrightness(data);

        tv.updateCharacteristic(this.Characteristic.Active, state.power ? this.Characteristic.Active.ACTIVE : this.Characteristic.Active.INACTIVE);
        light.updateCharacteristic(this.Characteristic.On, state.power);
        light.updateCharacteristic(this.Characteristic.Brightness, state.brightness);
      } catch (error) {
        this.log.warn(`NAS Monitoring Panel refresh failed: ${error.message}`);
      }
    };

    tv.getCharacteristic(this.Characteristic.Active)
      .onGet(async () => {
        await refresh();
        return state.power ? this.Characteristic.Active.ACTIVE : this.Characteristic.Active.INACTIVE;
      })
      .onSet(async (value) => {
        if (value === this.Characteristic.Active.ACTIVE) {
          await client.turnOn();
          state.power = true;
        } else {
          await client.turnOff();
          state.power = false;
        }
        await refresh();
      });

    light.getCharacteristic(this.Characteristic.On)
      .onGet(async () => {
        await refresh();
        return state.power;
      })
      .onSet(async (value) => {
        if (value) {
          await client.turnOn();
          state.power = true;
        } else {
          await client.turnOff();
          state.power = false;
        }
        await refresh();
      });

    light.getCharacteristic(this.Characteristic.Brightness)
      .onGet(async () => {
        await refresh();
        return state.brightness;
      })
      .onSet(async (value) => {
        await client.setBrightness(Number(value));
        state.brightness = Number(value);
        if (!state.power && Number(value) > 0) {
          await client.turnOn();
          state.power = true;
        }
        await refresh();
      });

    refresh();
    setInterval(refresh, Number(this.config.refreshSeconds || 15) * 1000);
  }
}

function normalizePower(data) {
  if (typeof data.power === 'boolean') {
    return data.power;
  }
  const state = String(data.state || '').toLowerCase();
  return state === 'on' || state === 'true' || state === '1';
}

function normalizeBrightness(data) {
  const raw = data.brightness ?? data.brightness_percent ?? 100;
  const num = Number(raw);
  if (Number.isNaN(num)) {
    return 100;
  }
  return Math.max(0, Math.min(100, Math.round(num)));
}

class PanelClient {
  constructor(options) {
    this.host = options.host;
    this.port = options.port;
    this.username = options.username;
    this.password = options.password;
    this.log = options.log;
    this.protocol = options.https ? 'https:' : 'http:';
    this.transport = options.https ? https : http;
  }

  async status() {
    return this.requestJson('/api/display/status');
  }

  async turnOn() {
    await this.requestText('/api/display/on');
  }

  async turnOff() {
    await this.requestText('/api/display/off');
  }

  async setBrightness(value) {
    const safe = Math.max(0, Math.min(100, Math.round(Number(value) || 0)));
    await this.requestText(`/api/display/brightness?value=${safe}`);
  }

  requestJson(path) {
    return this.request(path, true);
  }

  requestText(path) {
    return this.request(path, false);
  }

  request(path, parseJson) {
    const url = new URL(`${this.protocol}//${this.host}:${this.port}${path}`);
    const headers = {};
    if (this.password) {
      const auth = Buffer.from(`${this.username}:${this.password}`).toString('base64');
      headers.Authorization = `Basic ${auth}`;
    }

    return new Promise((resolve, reject) => {
      const req = this.transport.request(url, { method: 'GET', headers, timeout: 5000 }, (res) => {
        let body = '';
        res.setEncoding('utf8');
        res.on('data', (chunk) => { body += chunk; });
        res.on('end', () => {
          if (res.statusCode >= 400) {
            reject(new Error(`HTTP ${res.statusCode}: ${body}`));
            return;
          }
          try {
            resolve(parseJson ? JSON.parse(body) : body);
          } catch (error) {
            reject(new Error(`Invalid response: ${error.message}`));
          }
        });
      });

      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy(new Error('Request timed out'));
      });
      req.end();
    });
  }
}
