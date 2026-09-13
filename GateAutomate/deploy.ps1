scp .\configuration.yaml pi@raspberrypi.local:/tmp/configuration.yaml
$code1 = $LASTEXITCODE

if ($code1 -eq 0) {
    ssh pi@raspberrypi.local "sudo cp /home/pi/homeassistant/configuration.yaml /home/pi/homeassistant/configuration.yaml.bak && sudo mv /tmp/configuration.yaml /home/pi/homeassistant/configuration.yaml && sudo docker restart homeassistant"
} else {
    Write-Host "Deploy failed. Home Assistant not restarted."
}