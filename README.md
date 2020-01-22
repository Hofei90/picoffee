# picoffee
## Kurzbeschreibung
Die Software picoffee steuert die Freigabe für eine Kaffeemaschine bei Anmeldung eines Benutzers mittels 
RFID Chip und ausreichendem Guthaben.
Hardwareumsetzung kann natürlich unterschiedlich ausgeführt sein. In diesem Projekt ist es so realisiert, dass die 
Widerstände der Tastenplatine der Kaffeemaschine entlötet worden sind und diese über Relais zugeschaltet werden, 
gesteuert von picoffee.

## Software
### Benötigte Software
picoffee unterstützt Pythonversion >3.5.x

Benötigte Pythonmodule sind in der _requirements.txt_ gelistet.
 
### Installation
Paket unter gewünschten Verzeichnis abspeichern.

Zum Start von picoffee direkt die Datei _picoffee.py_ starten. Ein Autostart kann z.B mittels Systemd gelöst werden.
Beispiel siehe unter _picoffee.service_


## Komplette Projektvorstellung
Komplette Projektvorstellung unter: https://forum-raspberrypi.de/forum/thread/32856-kaffeemaschine-automatische-abrechnung/
