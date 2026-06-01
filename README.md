# CozyLife Sensors for Home Assistant

Custom Home Assistant integration for CozyLife temperature and humidity sensors.

It reads the CozyLife cloud API directly, without routing through SmartThings.

## Features

- UI configuration flow
- Temperature, humidity, and battery sensors
- One Home Assistant device per CozyLife sensor
- Cloud polling through the CozyLife API
- No SmartThings bridge required

## Supported devices

Confirmed:

- `Z4tRml` - temperature and humidity sensor, BL602

Reported by community projects:

- `s1AxFq` - Wi-Fi temperature and humidity sensor

The integration discovers any CozyLife device whose state exposes the temperature
and humidity datapoints.

## Entities

For each sensor, the integration creates:

- Temperature
- Humidity
- Battery

## Configuration

You need the same email and password used by the CozyLife app.

Country code depends on the account region. Confirmed values:

- Italy: `380`

## Installation

### HACS custom repository

After this repository is published on GitHub:

1. Open HACS.
2. Add this repository as a custom repository of type **Integration**.
3. Install **CozyLife Sensors**.
4. Restart Home Assistant.
5. Add **CozyLife Sensors** from Settings > Devices & services.

### Manual

Copy `custom_components/cozylife_sensors` into your Home Assistant
`custom_components` directory, restart Home Assistant, then add
**CozyLife Sensors** from Settings > Devices & services.

## Troubleshooting

### Invalid username or password

If the same credentials work in the CozyLife app, check the country code. For
Italian accounts, use `380`.

### Sensors update slowly

CozyLife sensors may report slowly to the cloud, depending on their own reporting
interval and battery-saving behavior. Polling more often cannot force the sensor
hardware to wake up.

### Device not found

Open an issue with sanitized device details:

- product ID
- model name
- firmware chip
- firmware version
- visible datapoint numbers

Do not share passwords, tokens, device keys, or full raw API responses.

## Development helper

`tools/cozylife_probe.js` can print sanitized device information from the
CozyLife API. It requires Node.js 18 or newer.

```sh
COZYLIFE_EMAIL="user@example.com" \
COZYLIFE_PASSWORD="password" \
COZYLIFE_COUNTRY_CODE="380" \
node tools/cozylife_probe.js
```

## Credits

The CozyLife API endpoints and datapoints are based on community research from:

- https://github.com/iam-medvedev/homebridge-cozylife-temperature-sensor
