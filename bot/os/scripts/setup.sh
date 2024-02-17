#!/bin/bash
sss_cache -u $1
touch /var/lib/systemd/linger/$1
export XDG_RUNTIME_DIR=/run/user/$(id -u $1)
systemctl --user -M $1@ daemon-reload
systemctl --user -M $1@ enable caddy
systemctl reload caddy