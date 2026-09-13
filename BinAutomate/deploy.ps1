$ErrorActionPreference = "Stop"

$RemoteHost = "pi@raspberrypi.local"
$RemoteConfigDir = "/home/pi/homeassistant"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

scp .\scripts\cardinia_bins.py "${RemoteHost}:/tmp/cardinia_bins.py"
scp .\scripts\enable_ha_packages.py "${RemoteHost}:/tmp/enable_ha_packages.py"
scp .\packages\cardinia_bins.yaml "${RemoteHost}:/tmp/cardinia_bins.yaml"

$remoteCommand = @"
set -eu
mkdir -p "$RemoteConfigDir/scripts" "$RemoteConfigDir/packages"
cp "$RemoteConfigDir/configuration.yaml" "$RemoteConfigDir/configuration.yaml.bak.$Stamp"
if [ -f "$RemoteConfigDir/packages/cardinia_bins.yaml" ]; then
  cp "$RemoteConfigDir/packages/cardinia_bins.yaml" "$RemoteConfigDir/packages/cardinia_bins.yaml.bak.$Stamp"
fi
mv /tmp/cardinia_bins.py "$RemoteConfigDir/scripts/cardinia_bins.py"
mv /tmp/enable_ha_packages.py "$RemoteConfigDir/scripts/enable_ha_packages.py"
mv /tmp/cardinia_bins.yaml "$RemoteConfigDir/packages/cardinia_bins.yaml"
chmod 755 "$RemoteConfigDir/scripts/cardinia_bins.py"
chmod 755 "$RemoteConfigDir/scripts/enable_ha_packages.py"
python3 "$RemoteConfigDir/scripts/enable_ha_packages.py" "$RemoteConfigDir/configuration.yaml"
docker exec homeassistant python -m homeassistant --script check_config --config /config
docker restart homeassistant
"@

ssh $RemoteHost $remoteCommand
