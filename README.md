# Heatmiser WiFi Time Sync

Home Assistant custom integration that synchronises the clock of legacy
Heatmiser Wi-Fi thermostats with Home Assistant's local time.

It supports multiple thermostats (including four independent devices), runs at
startup and periodically, and provides a manual sync button plus a last-sync
sensor for every thermostat.

## Why this tool exists

These thermostats are old (released in 2011) but works still very well, until they are fully working i cannot justify an additional expense for a newer device with the exact same features. Only drawback is Wifi speed limited to 802.11b and requires a separate wifi ssid/ap to not  bottleneck modern devices with latency. In my home they stay fine in an isolated VLAN/Dedicated Wifi AP together with Tuya crap

This tool was intentionally developed only for clock synchronisation. Home
Assistant already provides all the statistics, history, and data visualisation
needed for day-to-day monitoring, so duplicating the original project's
database and web interface would add unnecessary complexity.

For remote control of a single thermostat, the existing
[`heatmiser_wifi_ha`](https://github.com/iainbullock/heatmiser_wifi_ha) Home
Assistant integration can be used. When multiple thermostats must be
controlled, the recommended approach is to use HomeKit with
[`homebridge-heatmiser-ib`](https://github.com/iainbullock/homebridge-heatmiser-ib).
This project therefore does not duplicate thermostat controls and remains
focused on reliable clock synchronisation.

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

This fork was developed with ChatGPT for the design, implementation,
documentation, and initial validation of the Home Assistant integration.

The Heatmiser V3 protocol implementation is derived from Alexander
Thoukydides' GPL-3.0 `heatmiser-wifi` project:
https://github.com/thoukydides/heatmiser-wifi

This project is therefore licensed under GPL-3.0-or-later.
