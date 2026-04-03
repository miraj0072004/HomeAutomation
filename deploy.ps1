scp .\garage_server.py pi@raspberrypi.local:/home/pi/garage_server.py
$code1 = $LASTEXITCODE

scp .\garage.service pi@raspberrypi.local:/tmp/garage.service
$code2 = $LASTEXITCODE

if ($code1 -eq 0 -and $code2 -eq 0) {
    ssh pi@raspberrypi.local "sudo mv /tmp/garage.service /etc/systemd/system/garage.service && sudo systemctl daemon-reload && sudo systemctl restart garage && sudo systemctl status garage --no-pager"
} else {
    Write-Host "Deploy failed. Not restarting service."
}