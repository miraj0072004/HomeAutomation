scp .\garage_server.py pi@raspberrypi.local:/home/pi/garage_server.py
scp .\garage.service pi@raspberrypi.local:/tmp/garage.service

if ($LASTEXITCODE -eq 0) {
    ssh pi@raspberrypi.local "
        sudo mv /tmp/garage.service /etc/systemd/system/garage.service &&
        sudo systemctl daemon-reload &&
        sudo systemctl restart garage
    "
} else {
    Write-Host "Deploy failed. Not restarting service."
}