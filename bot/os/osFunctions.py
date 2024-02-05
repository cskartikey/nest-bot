import sys
import os


def generate_config(username):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(current_dir, "template", "etcFile.txt")
    with open(config_dir, "r") as file:
        config = file.read()
        config = config.replace("<username>", username)
        append_to_caddyfile(config)


def generate_configHome(username):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(current_dir, "template", "homeFile.txt")
    with open(config_dir, "r") as file:
        config = file.read()
        config = config.replace("<username>", username)
        write(username, config)


def append_to_caddyfile(config):
    with open("/etc/caddy/Caddyfile", "a") as caddyfile:
        caddyfile.write(config)


def write_to_home(username, config):
    caddyfile_path = f"/home/{username}/Caddyfile"
    with open(caddyfile_path, "r") as caddyfile:
        caddyfile.write(config)
