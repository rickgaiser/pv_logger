import threading
import time
from struct import *
from RF24 import *
from RF24Network import *
from emoncms import *

this_node = 00
other_node = 01

class CPulseDriver(threading.Thread):
	def __init__(self, ev):
		threading.Thread.__init__(self)
		self.ev = ev
		self.exitFlag = 0

		self.radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)
		self.network = RF24Network(self.radio)
		self.radio.begin()
		time.sleep(0.1)
		self.network.begin(90, this_node)
		self.radio.printDetails()

		self.start()

	def stop(self):
		self.exitFlag = 1
		self.join()

	def run(self):
		while not self.exitFlag:
			self.network.update()
			while self.network.available():
				header, payload_raw = self.network.read(12)
				payload = unpack('<4sLL', payload_raw)
				name = payload[0]
				millis = payload[1]
				value = payload[2]
				node = 'Node{}.{}'.format(oct(header.from_node), name)
				print '{}: {} = {}'.format(millis, node, value)
				WriteToEmoncms(node, value)
				if node == 'Node01.CNT0':
					self.ev.set()
			time.sleep(0.1)

#Simple test
#ev = threading.Event()
#drv = CPulseDriver(ev)
#time.sleep(10)
#drv.stop()
