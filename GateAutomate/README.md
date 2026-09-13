# GateAutomate

Garage door relay automation for the Raspberry Pi and Home Assistant.

GateAutomate exposes a small Flask HTTP service on the Raspberry Pi. Home Assistant calls that service through a `rest_command`, and the service briefly pulses GPIO 17 to trigger the garage door relay.

## Architecture

```text
iPhone Home Assistant app
  |
  | user taps garage control
  v
Home Assistant container on Raspberry Pi
  |
  | rest_command.trigger_garage
  v
http://100.72.98.73:5000/trigger?token=...
  |
  | Flask app running as garage.service
  v
garage_server.py
  |
  | GPIO17 LOW for 1 second, then HIGH
  v
Garage door relay
```

## Components

- `garage_server.py` - Flask relay service. It exposes `/trigger` and `/health`.
- `garage.service` - systemd unit that runs `garage_server.py` on the Pi.
- `configuration.yaml` - Home Assistant config snippet containing `rest_command.trigger_garage`.
- `deploy.ps1` - copies Home Assistant configuration to the Pi and restarts Home Assistant.
- `ReadMe.txt` - older quick notes.

## Runtime Behaviour

The relay service:

- Listens on `0.0.0.0:5000`.
- Requires the `SECRET_TOKEN` environment variable.
- Rejects `/trigger` requests with the wrong token.
- Pulses GPIO 17 for 1 second when triggered.
- Holds GPIO 17 HIGH when idle.
- Enforces a 10 second cooldown between successful triggers.
- Exposes `/health` for local checks.

The systemd service:

- Runs as user `pi`.
- Starts after the network is online.
- Restarts automatically if the Flask process exits.
- Provides `SECRET_TOKEN` to the app through the unit environment.

## Tailscale

Home Assistant currently calls the garage service through the Pi's Tailscale IP:

```yaml
rest_command:
  trigger_garage:
    url: "http://100.72.98.73:5000/trigger?token=..."
    method: GET
```

That means the garage command depends on the Pi being logged in to Tailscale. If Tailscale shows the Raspberry Pi as offline or `Needs login`, Home Assistant may not be able to reach the relay service at `100.72.98.73`.

Because Home Assistant and `garage_server.py` both run on the same Raspberry Pi, a future improvement would be to route this call locally instead of through Tailscale. Tailscale would still be useful for remote access, but the garage trigger itself would be less fragile.

## Useful Pi Checks

Check whether Tailscale is healthy:

```bash
sudo systemctl status tailscaled
tailscale status
```

If Tailscale needs login:

```bash
sudo tailscale up
```

Check whether the garage relay service is running:

```bash
sudo systemctl status garage.service
```

Check whether the Flask service responds locally:

```bash
curl http://127.0.0.1:5000/health
```

View recent service logs:

```bash
journalctl -u garage.service -n 100 --no-pager
```

Restart the garage service:

```bash
sudo systemctl restart garage.service
```

## Deploy Notes

From Windows:

```powershell
cd C:\Work\Python\HomeAutomate\GateAutomate
.\deploy.ps1
```

Be careful with `deploy.ps1`: it replaces the live Home Assistant `configuration.yaml` on the Pi. If the live Home Assistant config has changes that are not in this repo, copy or merge them first.

The garage relay service itself is separate from the Home Assistant container. Updating Home Assistant configuration does not automatically update `garage_server.py` or `garage.service`.

## Safety Notes

- Do not expose port `5000` directly to the public internet.
- Keep the trigger token private.
- Use the cooldown to avoid accidental repeated relay pulses.
- Prefer testing `/health` before testing `/trigger`.
- Avoid editing the garage relay code while standing near the moving door.
