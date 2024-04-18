#!/bin/bash
shopt -s dotglob
cp -r /etc/skel/* /home/$1
chown -R $1:$(id -u $1) /home/$1
chown $1:1001 /home/$1
chown $1:1001 /home/$1/Caddyfile
chmod 770 /home/$1
chmod 770 /home/$1/Caddyfile
systemctl --user -M $1@ daemon-reload