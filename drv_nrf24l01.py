import time
from struct import *
from RF24 import *
from RF24Network import *

radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)
network = RF24Network(radio)

this_node = 00
other_node = 01

radio.begin()
time.sleep(0.1)
network.begin(90, this_node)
radio.printDetails()

while 1:
	network.update()
	while network.available():
		header, payload_raw = network.read(4)
		payload = unpack('<i', payload_raw)
		print 'Power: ', payload[0], 'wh, from ', oct(header.from_node)
	time.sleep(0.1)
