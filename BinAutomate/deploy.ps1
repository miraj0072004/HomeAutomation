$ErrorActionPreference = "Stop"

$RemoteHost = "pi@raspberrypi.local"
$RemoteConfigDir = "/home/pi/homeassistant"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$RemoteDeployScript = "/tmp/deploy_cardinia_bins.sh"
$LocalDeployScript = Join-Path $env:TEMP "deploy_cardinia_bins.sh"

scp .\scripts\cardinia_bins.py "${RemoteHost}:/tmp/cardinia_bins.py"
scp .\scripts\enable_ha_packages.py "${RemoteHost}:/tmp/enable_ha_packages.py"
scp .\packages\cardinia_bins.yaml "${RemoteHost}:/tmp/cardinia_bins.yaml"

$remoteScript = @"
set -eu
sudo mkdir -p "$RemoteConfigDir/scripts" "$RemoteConfigDir/packages"
sudo cp "$RemoteConfigDir/configuration.yaml" "$RemoteConfigDir/configuration.yaml.bak.$Stamp"
if [ -f "$RemoteConfigDir/packages/cardinia_bins.yaml" ]; then
  sudo cp "$RemoteConfigDir/packages/cardinia_bins.yaml" "$RemoteConfigDir/packages/cardinia_bins.yaml.bak.$Stamp"
fi
sudo install -m 755 /tmp/cardinia_bins.py "$RemoteConfigDir/scripts/cardinia_bins.py"
sudo install -m 755 /tmp/enable_ha_packages.py "$RemoteConfigDir/scripts/enable_ha_packages.py"
sudo install -m 644 /tmp/cardinia_bins.yaml "$RemoteConfigDir/packages/cardinia_bins.yaml"
sudo python3 "$RemoteConfigDir/scripts/enable_ha_packages.py" "$RemoteConfigDir/configuration.yaml"
sudo docker exec homeassistant python -m homeassistant --script check_config --config /config
sudo docker restart homeassistant
"@

$remoteScript = $remoteScript -replace "`r`n", "`n"
[System.IO.File]::WriteAllText($LocalDeployScript, $remoteScript, [System.Text.UTF8Encoding]::new($false))

scp $LocalDeployScript "${RemoteHost}:${RemoteDeployScript}"
ssh $RemoteHost "bash ${RemoteDeployScript}"
