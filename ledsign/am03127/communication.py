# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Communication with AM03127-based LED signs
"""

from .messages import *
import datetime
import serial
import time

class SerialCommunicator(object):
	"""
	Manager class for serial communication with the LED Sign
	"""
	
	BYTESIZE = serial.EIGHTBITS
	PARITY = serial.PARITY_NONE
	STOPBITS = serial.STOPBITS_ONE
	
	PROCESSING_TIME = 0.5 # How long we should wait between sending a command and reading the response
	
	def __init__(self, port, baudrate, timeout):
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout
		self.init_comm()
	
	def init_comm(self):
		self.device = serial.serial_for_url(self.port,
			baudrate = self.baudrate,
			bytesize = self.BYTESIZE,
			parity = self.PARITY,
			stopbits = self.STOPBITS,
			timeout = self.timeout,
			writeTimeout = self.timeout
		)
	
	def blocking_write(self, data):
		"""
		Perform a write operation and wait until it's likely to have finished
		"""
		
		num_bytes = self.device.write(data)
		return num_bytes
	
	def send_command(self, data):
		"""
		Send data to the device, wait for it to process the data and read the response
		"""
		
		self.blocking_write(data)
		time.sleep(self.PROCESSING_TIME)
		response = self.device.read(self.device.inWaiting())
		return response

class LEDSign(object):
	"""
	LED Sign class, for actually interfacing with the sign
	"""
	
	EFFECT_IMMEDIATE = "A"
	EFFECT_XOPEN = "B"
	EFFECT_CURTAIN_UP = "C"
	EFFECT_CURTAIN_DOWN = "D"
	EFFECT_SCROLL_LEFT = "E"
	EFFECT_SCROLL_RIGHT = "F"
	EFFECT_VOPEN = "G"
	EFFECT_VCLOSE = "H"
	EFFECT_SCROLL_UP = "I"
	EFFECT_SCROLL_DOWN = "J"
	EFFECT_HOLD = "K"
	EFFECT_SNOW = "L"
	EFFECT_TWINKLE = "M"
	EFFECT_BLOCK_MOVE = "N"
	EFFECT_RANDOM = "P"
	EFFECT_HELLO_WORLD = "Q"
	EFFECT_WELCOME = "R"
	EFFECT_AMPLUS = "S"
	
	METHOD_NORMAL = 0x01
	METHOD_BLINKING = 0x02
	METHOD_SONG_1 = 0x03
	METHOD_SONG_2 = 0x04
	METHOD_SONG_3 = 0x05
	
	SPEED_FAST = 0x40
	SPEED_MEDIUM = 0x50
	SPEED_SLOW = 0x60
	SPEED_SLOWEST = 0x70
	
	def __init__(self, port = None, baudrate = 9600, timeout = None, id = 1):
		self.id = id
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout
		self.comm = SerialCommunicator(
			port = port,
			baudrate = baudrate,
			timeout = timeout
		)
	
	def _get_page_char(self, page):
		return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[page - 1]
	
	def _get_schedule_char(self, schedule):
		return "ABCDE"[schedule - 1]
	
	def _get_wait_char(self, duration):
		if duration < 1.0:
			char = "A"
		else:
			char = "BCDEFGHIJKLMNOPQRSTUVWXYZ"[int(duration) - 1]
		return char
	
	def send_raw(self, data, expected_response = "ACK"):
		"""
		Send the given data to the sign, read the response, decide whether the sign
		acknowledges the data and return a boolean indicating success or failure
		"""
		
		response = self.comm.send_command(data)
		# print repr(response)
		
		if response == expected_response:
			success = True
		else:
			success = False
		
		return success
	
	def send_message(self, message):
		"""
		Send a message instance to the sign
		"""
		
		message.set_id(self.id)
		# print message.render()
		
		if isinstance(message, SetIDMessage):
			expected_response = "%02X" % message.format_data['id']
		else:
			expected_response = "ACK"
		
		success = self.send_raw(message.render(), expected_response)
		return success
	
	def set_id(self, id):
		"""
		Set the sign's ID
		"""
		
		msg = SetIDMessage(id = id)
		return self.send_message(msg)
	
	def set_clock(self, timedata = None):
		"""
		Set the sign's internal clock
		"""
		
		if timedata is None:
			timedata = datetime.datetime.now()
		
		msg = SetClockMessage(
			year = timedata.strftime("%y"),
			weekday = timedata.isoweekday(),
			month = timedata.month,
			day = timedata.day,
			hour = timedata.hour,
			minute = timedata.minute,
			second = timedata.second
		)
		return self.send_message(msg)
	
	def send_page(self, content, page = "A", line = 1, lead = EFFECT_SCROLL_LEFT, speed = SPEED_MEDIUM, method = METHOD_NORMAL, wait = 2.0, lag = EFFECT_SCROLL_LEFT):
		"""
		Send text to a page
		"""
		
		if not isinstance(content, PageContent):
			content = PageContent(content)
		
		if type(page) not in (str, unicode):
			page = self._get_page_char(page)
		
		if type(wait) not in (str, unicode):
			wait = self._get_wait_char(wait)
		
		if type(method) not in (str, unicode):
			method = chr(speed + method)
		
		msg = SendPageMessage(
			line = line,
			page = page.upper(),
			lead = lead,
			method = method,
			wait = wait.upper(),
			lag = lag,
			content = content.render()
		)
		return self.send_message(msg)
	
	def send_schedule(self, schedule = "A", start = None, end = None, pages = "A", recurring = False):
		"""
		Send a schedule
		"""
		
		if start is None:
			start = datetime.datetime(
				year = 2000,
				month = 1,
				day = 1
			)
		
		if end is None:
			end = datetime.datetime(
				year = 2099,
				month = 12,
				day = 31
			)
		
		if recurring:
			startyear = 0
			startmonth = 0
			startday = 0
			starthour = start.hour
			startminute = start.minute
			endyear = 0
			endmonth = 0
			endday = 0
			endhour = end.hour
			endminute = end.minute
		else:
			startyear = int(start.strftime("%y"))
			startmonth = start.month
			startday = start.day
			starthour = start.hour
			startminute = start.minute
			endyear = int(end.strftime("%y"))
			endmonth = end.month
			endday = end.day
			endhour = end.hour
			endminute = end.minute
		
		if type(schedule) not in (str, unicode):
			schedule = self._get_schedule_char(schedule)
		
		msg = SendScheduleMessage(
			schedule = schedule.upper(),
			startyear = startyear,
			startmonth = startmonth,
			startday = startday,
			starthour = starthour,
			startminute = startminute,
			endyear = endyear,
			endmonth = endmonth,
			endday = endday,
			endhour = endhour,
			endminute = endminute,
			pages = pages.upper()
		)
		return self.send_message(msg)
	
	def delete_page(self, page, line):
		"""
		Delete a page
		"""
		
		if type(page) not in (str, unicode):
			page = self._get_page_char(page)
		
		msg = DeletePageMessage(
			page = page,
			line = line
		)
		return self.send_message(msg)
	
	def delete_schedule(self, schedule):
		"""
		Delete a schedule
		"""
		
		if type(schedule) not in (str, unicode):
			schedule = self._get_schedule_char(schedule)
		
		msg = DeleteScheduleMessage(
			schedule = schedule
		)
		return self.send_message(msg)
	
	def delete_all(self):
		"""
		Delete all data
		"""
		
		msg = DeleteAllMessage()
		return self.send_message(msg)
	
	def set_run_page(self, page):
		"""
		Set the default run page
		"""
		
		if type(page) not in (str, unicode):
			page = self._get_page_char(page)
		
		msg = SetRunPageMessage(
			page = page
		)
		return self.send_message(msg)
	
	def set_brightness(self, level):
		"""
		Set the LED brightness
		"""
		
		if type(level) not in (str, unicode):
			level = "ABCDD"[4 - int(divmod(level, 0.25)[0])]
		
		msg = SetBrightnessMessage(
			level = level
		)
		return self.send_message(msg)
	
	def reset_character_table(self):
		"""
		Reset the character table to the factory default
		"""
		
		msg = ResetCharacterTableMessage()
		return self.send_message(msg)