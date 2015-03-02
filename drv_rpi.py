import Queue
import threading
import time
import RPi.GPIO as GPIO

time_last_pulse = 0
time_prev_pulse = 0
pulse_counter = 0
power_max = 0

# Create condition for notifying main thread of new data
ev = threading.Event()

class CKWH_Driver_rpi(threading.Thread):
	def __init__(self, q):
		threading.Thread.__init__(self)
		self.q = q
		self.exitFlag = 0
		self.wh = 0
		
		# Setup raspberry pi gpio input event handler
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
		GPIO.add_event_detect(23, GPIO.RISING, callback=eventRising, bouncetime=300)

	def stop(self):
		GPIO.remove_event_detect(23)
		GPIO.cleanup()
		self.exitFlag = 1

	def run(self):
		while not self.exitFlag:
			if ev.wait(1) == True:
				ev.clear()
				self.wh += 1
				self.q.put(self.wh)
				print 'Power: ', self.wh, 'wh'

def eventRising(channel):
	input = GPIO.input(channel)
	if(input == 1):
		ev.set()

'Simple test
'workQueue = Queue.Queue(10)
'drv = CKWH_Driver_rpi(workQueue)
'drv.start()
'time.sleep(10)
'drv.stop()
'drv.join()
