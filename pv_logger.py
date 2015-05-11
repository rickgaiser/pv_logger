#import drv_sim
#import drv_rpi
import drv_nrf24l01
import time
from time import localtime, strftime
import thread
import threading
import subprocess
import logging
from config import *
from emoncms import *

time_last_pulse = 0
time_prev_pulse = 0
pulse_counter = 0
pulse_counter_logged = 0
power = 0
power_max = 0

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
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
logger.info('Started')

# Start pulse driver
pulse_ev = threading.Event()
#drv = drv_sim.CPulseDriver(pulse_ev)
#drv = drv_rpi.CPulseDriver(pulse_ev)
drv = drv_nrf24l01.CPulseDriver(pulse_ev)

# Write to PVOutput.org
def WriteToPVOutput(dt, wh, wmax):
	t_date   = 'd={0}'.format(time.strftime("%Y%m%d", time.localtime(dt)))
	t_time   = 't={0}'.format(time.strftime("%H:%M",  time.localtime(dt)))
	t_energy = 'v1={0}'.format(wh)
	t_power  = 'v2={0:.0f}'.format(wmax)
	cmd = ['/usr/bin/curl',
		'-d', t_date,
		'-d', t_time,
		'-d', t_energy,
		'-d', t_power,
		'-H', 'X-Pvoutput-Apikey: ' + PVOUTPUT_APIKEY,
		'-H', 'X-Pvoutput-SystemId: ' + PVOUTPUT_SYSTEMID,
		'http://pvoutput.org/service/r2/addstatus.jsp']
	subprocess.call (cmd)

# Write to emoncms.org
def WriteToEmoncms_wh(wh, power):
	WriteToEmoncms('wh', wh)
	WriteToEmoncms('power', power)

# Start main loop
time_last_log = time.time()
time_last_pulse = time.time()
exitFlag = False
while not exitFlag:
	try:
		event = pulse_ev.wait(1)
		event_time = time.time()
		if event == True:
			pulse_ev.clear()

			time_prev_pulse = time_last_pulse
			time_last_pulse = event_time
			pulse_counter += 1
			if time_prev_pulse != 0:
				time_elapsed = time_last_pulse - time_prev_pulse
				power = (3600 / time_elapsed)
				if power > power_max:
					power_max = power
				thread.start_new_thread(WriteToEmoncms_wh, (pulse_counter, power))
				logger.info("{0}Wh: {1:.2f}sec = {2:.0f}Watt".format(pulse_counter, time_elapsed, power))
			else:
				logger.info("{0}Wh".format(pulse_counter))

		# Try to log every 5 minutes
		if ((time.localtime(event_time).tm_min % 5) == 0) and ((event_time - time_last_log) > (1*60)):
			# Log only when new data is available
			if (pulse_counter > pulse_counter_logged):
				thread.start_new_thread(WriteToPVOutput, (time_last_pulse, pulse_counter, power_max))
				logger.info('Upload to PVOutput: {0}Wh, {1:.0f}W piek'.format(pulse_counter, power_max))

				pulse_counter_logged = pulse_counter
				power_max = 0

			time_last_log = event_time

		# End of day if no enery for more than 1 hour
		if (pulse_counter > 0) and ((event_time - time_last_pulse) > (60*60)):
			pulse_counter = 0
			pulse_counter_logged = 0
			time_prev_pulse = 0
			time_last_pulse = 0
			logger.info('END OF DAY')

	except KeyboardInterrupt:
		logger.info('Stopping')
		exitFlag = True

# Stop pulse driver
drv.stop()
