# BinAutomate

Cardinia bin collection reminders for Home Assistant.

This project creates `sensor.cardinia_bin_collections` from Cardinia's live collection-zone data and sends Sunday 10am and 7pm notifications to `notify.mobile_app_mirajs_iphone` when bins are due the next morning.

## Files

- `scripts/cardinia_bins.py` - resolves the address and computes next rubbish, recycling, and green-waste dates.
- `scripts/enable_ha_packages.py` - idempotently enables `homeassistant: packages` in Home Assistant.
- `packages/cardinia_bins.yaml` - Home Assistant command-line sensor and automations.
- `deploy.ps1` - additive deploy to `pi@raspberrypi.local` with backups and Home Assistant config validation.

## Manual dashboard check

After deploying, add a dashboard button that calls `script.check_cardinia_bin_status`.

```yaml
type: button
name: Check bins
icon: mdi:trash-can-outline
tap_action:
  action: call-service
  service: script.check_cardinia_bin_status
```

Tapping it refreshes `sensor.cardinia_bin_collections` and sends a push notification with the current bin status.

## Deploy

```powershell
.\deploy.ps1
```

The deploy script backs up live config files, runs Home Assistant `check_config`, and restarts the Home Assistant container only after validation succeeds.
