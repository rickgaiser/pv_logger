import threading
import time
import RPi.GPIO as GPIO

# Create condition for notifying main thread of new data
global_ev

class CPulseDriver(threading.Thread):
	def __init__(self, ev):
		threading.Thread.__init__(self)
		global_ev = ev

		# Setup raspberry pi gpio input event handler
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
		GPIO.add_event_detect(23, GPIO.RISING, callback=eventRising, bouncetime=300)

	def stop(self):
		GPIO.remove_event_detect(23)
		GPIO.cleanup()

def eventRising(channel):
	input = GPIO.input(channel)
	if(input == 1):
		#print('Pulse')
		global_ev.set()

#Simple test
#ev = threading.Event()
#drv = CPulseDriver(ev)
#time.sleep(10)
#drv.stop()
