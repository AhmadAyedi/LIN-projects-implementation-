import can
import logging
import subprocess

logger = logging.getLogger('can.listener')
logger.setLevel(logging.INFO)

commande = "sudo ip link set can0 up type can bitrate 500000"
resultat = subprocess.run(commande, shell=True, capture_output=True, text=True)
print(resultat.stdout)
bustype = 'socketcan'
channel = 'can0'
# setting up the can bus
bus = can.interface.Bus(channel=channel, bustype=bustype,bitrate=500000)



def message_handler(msg):
    logger.info(msg)

notifier = can.Notifier(bus, [can.Logger('can.log'), message_handler])
help(notifier)

notifier.stop()