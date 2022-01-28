#!/bin/sh
cd "$(dirname "$0")";
CWD="$(pwd)"
WAI="$(whoami)"
echo $CWD
echo $WAI

RCLONE_CONFIG=/home/pi/.config/rclone/rclone.conf
export RCLONE_CONFIG
python3 /home/pi/pictureFrame.py
