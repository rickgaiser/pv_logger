import RPi.GPIO as GPIO
import time
from time import localtime, strftime
import threading
import subprocess
import logging


from elogger_config import *


time_last_pulse = 0
time_prev_pulse = 0
pulse_counter = 0
power_max = 0

# Create condition for notifying main thread of new data
cond = threading.Condition()

# Create logger
logger = logging.getLogger('pv_logger')
logger.setLevel(logging.DEBUG)
# create file handler
fh = logging.FileHandler('pv_logger.log')
fh.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
logger.info('Started')

# Setup raspberry pi gpio input event handler
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.add_event_detect(23, GPIO.RISING, callback=printRising, bouncetime=300)


def printRising(channel):
	global time_last_pulse
	global time_prev_pulse
	global pulse_counter
	global power_max
	global cond
	global logger

	input = GPIO.input(channel)
	if (input == 1):
		cond.acquire()
		time_prev_pulse = time_last_pulse
		time_last_pulse = time.time()
		pulse_counter += 1
		if time_prev_pulse != 0:
			time_elapsed = time_last_pulse - time_prev_pulse
			power = (3600 / time_elapsed)
			if power > power_max:
				power_max = power
			logger.info("{0}Wh: {1:.2f}sec = {2:.0f}Watt".format(pulse_counter, time_elapsed, power))
		else:
			logger.info("{0}Wh".format(pulse_counter))
		cond.notify()
		cond.release()
	else:
		logger.warn("{0}Wh: (input={1})".format(pulse_counter, input))
	return


time_last_log = time.time()
pulse_counter_logged = 0
while True:
	cond.acquire()
	cond.wait(5)
	time = time.time()
	# Log if:
	# - There is new energy data
	# - The time is a multiple of 5 minutes
	# - At least 1 minutes have passed
	if (pulse_counter > pulse_counter_logged) and ((time.localtime(time).tm_min % 5) == 0) and ((time - time_last_log) > (1*60)):
		pulse_counter_logged = pulse_counter
		time_last_pulse_logged = time_last_pulse
		power_max_logged = power_max
		power_max = 0
		cond.release()

		time_last_log = time

		# Log to PVOutput
		t_date   = 'd={0}'.format(time.strftime("%Y%m%d", time.localtime(time_last_pulse_logged)))
		t_time   = 't={0}'.format(time.strftime("%H:%M",  time.localtime(time_last_pulse_logged)))
		t_energy = 'v1={0}'.format(pulse_counter_logged)
		t_power  = 'v2={0:.0f}'.format(power_max_logged)
		cmd = ['/usr/bin/curl',
			'-d', t_date,
			'-d', t_time,
			'-d', t_energy,
			'-d', t_power,
			'-H', 'X-Pvoutput-Apikey: ' + PVOUTPUT_APIKEY,
			'-H', 'X-Pvoutput-SystemId: ' + PVOUTPUT_SYSTEMID,
			'http://pvoutput.org/service/r1/addstatus.jsp']
		subprocess.call (cmd)
		logger.info('Upload to PVOutput: {0}Wh, {1:.0f}W piek'.format(pulse_counter_logged, power_max_logged))
	else:
		cond.release()

	# End of day if:
	# - No enery for more than 1 hour
	if (pulse_counter > 0) and ((time - time_last_log) > (60*60)):
		cond.acquire()
		pulse_counter = 0
		pulse_counter_logged = 0
		time_prev_pulse = 0
		time_last_pulse = 0
		cond.release()
		logger.info('END OF DAY')


GPIO.remove_event_detect(23)
GPIO.cleanup()
