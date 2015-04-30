import subprocess
from config import *

# Write to emoncms.org
def WriteToEmoncms(key, value):
	cmd = ['/usr/bin/curl',
		'http://emoncms.org/input/post.json?json={{{}:{}}}&apikey={}'.format(key, value, EMONCMS_APIKEY)]
	subprocess.call (cmd)

