import threading
import time

class CPulseDriver(threading.Thread):
	def __init__(self, ev):
		threading.Thread.__init__(self)
		self.ev = ev
		self.exitFlag = 0
		self.start()

	def stop(self):
		self.exitFlag = 1
		self.join()

	def run(self):
		while not self.exitFlag:
			time.sleep(1)
			#print('Pulse')
			self.ev.set()

#Simple test
#ev = threading.Event()
#drv = CPulseDriver(ev)
#time.sleep(10)
#drv.stop()
