import Queue
import threading
import time
from struct import *
from RF24 import *
from RF24Network import *

this_node = 00
other_node = 01

class CKWH_Driver_nrf24l01(threading.Thread):
	def __init__(self, q):
		threading.Thread.__init__(self)
		self.q = q
		self.exitFlag = 0
		self.wh_base = -1

		self.radio = RF24(RPI_V2_GPIO_P1_15, BCM2835_SPI_CS0, BCM2835_SPI_SPEED_8MHZ)
		self.network = RF24Network(self.radio)
		
		self.radio.begin()
		time.sleep(0.1)
		self.network.begin(90, this_node)
		self.radio.printDetails()
		
	def stop(self):
		self.exitFlag = 1

	def run(self):
		while not self.exitFlag:
			self.network.update()
			while self.network.available():
				header, payload_raw = self.network.read(4)
				payload = unpack('<i', payload_raw)
				wh = payload[0]
				if self.wh_base == -1:
					self.wh_base = wh - 1
				self.q.put(wh - self.wh_base)
				print 'Power: ', wh, 'wh, from ', oct(header.from_node)
			time.sleep(0.1)

'Simple test
'workQueue = Queue.Queue(10)
'drv = CKWH_Driver_nrf24l01(workQueue)
'drv.start()
'time.sleep(10)
'drv.stop()
'drv.join()
