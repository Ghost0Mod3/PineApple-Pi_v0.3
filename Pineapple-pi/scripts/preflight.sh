#!/usr/bin/env bash
set -u
echo "Pineapple-Pi preflight";hostname;nmcli device status;ip route show default;rpi-connect status 2>&1||true
printf 'wlan1 MAC: ';cat /sys/class/net/wlan1/address 2>/dev/null||echo missing
printf 'wlan1 driver: ';basename "$(readlink -f /sys/class/net/wlan1/device/driver 2>/dev/null)" 2>/dev/null||echo missing
printf 'wlan2: ';test -e /sys/class/net/wlan2&&echo detected||echo not-installed
