# Heatmiser WiFi Time Sync

Home Assistant custom integration that synchronises the clock of legacy
Heatmiser Wi-Fi thermostats with Home Assistant's local time.

It supports multiple thermostats (including four independent devices), runs at
startup and periodically, and provides a manual sync button plus a last-sync
sensor for every thermostat.

## Supported devices

- PRT-TS WiFi / PRT-TS WiFi RF
- PRTHW-TS WiFi / PRTHW-TS WiFi RF
- PRT-ETS WiFi

It does **not** support Heatmiser Neo, DT-TS WiFi, Multi-Link, Netmonitor, or
wired-only models.

## Installation with HACS

1. In HACS, open **Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add this repository URL and select category **Integration**.
4. Install **Heatmiser WiFi Time Sync** and restart Home Assistant.
5. Go to **Settings > Devices & services > Add integration** and search for
   **Heatmiser WiFi Time Sync**.
6. Add each thermostat separately. Repeat the flow four times for four devices.

The default TCP port is `8068`; the default PIN is `0000`. The PIN is stored in
the Home Assistant config entry and is never exposed as an entity attribute.

## Behaviour

- Synchronises once when Home Assistant starts (configurable).
- Repeats every 6 hours by default (configurable from 1 to 168 hours).
- Uses Home Assistant's configured timezone, including DST changes.
- Continues operating other thermostats if one device is offline.
- Exposes a **Synchronise clock** button and a **Last successful sync** sensor.

## Credits and licence

The Heatmiser V3 protocol implementation is derived from Alexander
Thoukydides' GPL-3.0 `heatmiser-wifi` project:
https://github.com/thoukydides/heatmiser-wifi

This project is therefore licensed under GPL-3.0-or-later.
