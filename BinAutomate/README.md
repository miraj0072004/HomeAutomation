# BinAutomate

Cardinia bin collection reminders for Home Assistant.

This project creates `sensor.cardinia_bin_collections` from Cardinia's live collection-zone data and sends a 7pm notification to `notify.mobile_app_mirajs_iphone` when bins are due the next morning.

## Files

- `scripts/cardinia_bins.py` - resolves the address and computes next rubbish, recycling, and green-waste dates.
- `scripts/enable_ha_packages.py` - idempotently enables `homeassistant: packages` in Home Assistant.
- `packages/cardinia_bins.yaml` - Home Assistant command-line sensor and automations.
- `deploy.ps1` - additive deploy to `pi@raspberrypi.local` with backups and Home Assistant config validation.

## Deploy

```powershell
.\deploy.ps1
```

The deploy script backs up live config files, runs Home Assistant `check_config`, and restarts the Home Assistant container only after validation succeeds.