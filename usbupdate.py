#!/usr/bin/python3
"""Skript zum automatischen Programmupdate wenn ein USB Stick angesteckt wird"""

import toml
import os
import subprocess

skriptpfad = str(os.path.abspath(os.path.dirname(__file__))) + "/"
usbpfad = "/mnt/usbstick/"
print(os.getcwd())
#Dateistruktur erstellen, anschließend auskommentieren
"""
config = dict()
config["usbpi"] = ["datei.py", "datei2.py"]
config["piusb"] = ["db.sql"]
ausgabe = config
ausgabe = toml.dumps(ausgabe)
with open("./conf.toml", "w") as file:
    file.write(ausgabe)"""


# # # # # # # # # #
#Config
# # # # # # # # # #
pfad = os.path.abspath(os.path.dirname(__file__))
configfile = pfad + "/conf.toml"
with open(configfile) as conffile:
    config = toml.loads(conffile.read())

# # # # # # # # # #
# Programm
# # # # # # # # # #
inhaltusb = set(os.listdir(usbpfad))
inhaltgelistet = set(config["usbpi"])
zukopieren = inhaltusb & inhaltgelistet
#Von USB Stick auf Pi kopieren
for datei in zukopieren:
    subprocess.Popen(["cp", usbpfad + datei, skriptpfad])
#Von Pi auf USB kopieren
zukopieren = config["piusb"]
for datei in zukopieren:
    subprocess.Popen(["cp", skriptpfad + datei, usbpfad])