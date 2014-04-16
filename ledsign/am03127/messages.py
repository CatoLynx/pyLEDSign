# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
Message types for AM03127-based LED signs
"""

class RawMessage(object):
	"""
	A raw datagram that can be sent to the sign, with all the various properties
	This class is usually instantiated by a LEDSign instance which fills in the ID field
	"""
	
	BASE_FORMAT = "<ID%(id)02X>%(data)s%(checksum)02X<E>"
	
	def __init__(self, id, data):
		self.format_data = {
			'id': id,
			'data': data,
			'checksum': 0
		}
	
	def calculate_checksum(self):
		for char in self.format_data['data']:
			self.format_data['checksum'] ^= ord(char)
	
	def render(self):
		self.calculate_checksum()
		return self.BASE_FORMAT % self.format_data

class SetIDMessage(RawMessage):
	"""
	A datagram to set the sign's ID. Differs from all other datagram types in that
	it doesn't have a checksum or ID field
	"""
	
	BASE_FORMAT = "<ID><%(id)02X><E>"
	
	def __init__(self, id):
		self.format_data = {
			'id': id
		}
	
	def set_id(self, id):
		"""
		For compatibility only
		"""
		
		return
	
	def render(self):
		return self.BASE_FORMAT % self.format_data

class BaseMessage(object):
	"""
	A template for datagrams that already includes the raw formatting
	As with RawMessage, the ID field is filled in by the LEDSign instance
	the moment it renders the message
	"""
	
	TEMPLATE = ""
	
	def __init__(self, id = 0, **data):
		self.id = id
		self.format_data = data
	
	def set_id(self, id):
		self.id = id
	
	def render(self):
		self.formatted_data = self.TEMPLATE % self.format_data
		msg = RawMessage(id = self.id, data = self.formatted_data)
		return msg.render()

class SetClockMessage(BaseMessage):
	"""
	Set the clock in the LED sign
	"""
	
	TEMPLATE = "<SC>%(year)02i%(weekday)02i%(month)02i%(day)02i%(hour)02i%(minute)02i%(second)02i"

class SendPageMessage(BaseMessage):
	"""
	Send a message to a page
	"""
	
	TEMPLATE = "<L%(line)i><P%(page)c><F%(lead)c><M%(method)c><W%(wait)c><F%(lag)c>%(content)s"

class SendScheduleMessage(BaseMessage):
	"""
	Send a schedule to the LED sign
	"""
	
	TEMPLATE = "<T%(schedule)c>%(startyear)02i%(startmonth)02i%(startday)02i%(starthour)02i%(startminute)02i%(endyear)02i%(endmonth)02i%(endday)02i%(endhour)02i%(endminute)02i%(pages)s"

class SendGraphicMessage(BaseMessage):
	"""
	Send a graphic to the LED sign
	"""
	
	TEMPLATE = "<G%(page)c%(block)i>%(data)s"

class DeletePageMessage(BaseMessage):
	"""
	Delete a page
	"""
	
	TEMPLATE = "<DL%(line)iP%(page)c>"

class DeleteScheduleMessage(BaseMessage):
	"""
	Delete a schedule
	"""
	
	TEMPLATE = "<DT%(schedule)c>"

class DeleteAllMessage(BaseMessage):
	"""
	Delete all data
	"""
	
	TEMPLATE = "<D*>"

class SetRunPageMessage(BaseMessage):
	"""
	Set the default page to run if no schedule is active
	"""
	
	TEMPLATE = "<RP%(page)c>"

class SetBrightnessMessage(BaseMessage):
	"""
	Set the brightness of the LED sign
	"""
	
	TEMPLATE = "<B%(level)c>"

class SendCharacterMessage(BaseMessage):
	"""
	Send a special character definition
	"""
	
	TEMPLATE = "<F%(font)c%(code)02X>%(data)s"

class ResetCharacterTableMessage(BaseMessage):
	"""
	Revert to the factory default special character table
	"""
	
	TEMPLATE = "<DU>"

class PageContent(object):
	"""
	A subclass representing the content of a page used in SendPageMessage
	"""
	
	def __init__(self, data):
		self.data = data
	
	def render(self):
		rendered_message = ""
		for part in self.data:
			if type(part) is not dict:
				rendered_message += part
				continue
			
			for key, value in part.iteritems():
				if key == 'text':
					rendered_message += value
					continue
				
				try:
					func = getattr(self, '_get_%s_tag' % key)
				except AttributeError:
					continue
				if type(value) is dict:
					tag = func(**value)
				else:
					tag = func(value)
				rendered_message += tag
		return rendered_message
	
	@classmethod
	def _get_font_tag(cls, font):
		if font == 'normal':
			char = "A"
		elif font == 'bold':
			char = "B"
		elif font == 'narrow':
			char = "C"
		elif font == 'large':
			char = "D"
		elif font == 'long':
			char = "E"
		else:
			char = "A"
		return "<A%c>" % char
	
	@classmethod
	def _get_bell_tag(cls, bell):
		try:
			bell = float(bell)
		except (TypeError, ValueError):
			bell = 1.0
		
		char = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[int(bell * 2 + 0.5) - 1]
		return "<B%c>" % char
	
	@classmethod
	def _get_color_tag(cls, color):
		if color == 'dim-red':
			char = "A"
		elif color == 'red':
			char = "B"
		elif color == 'bright-red':
			char = "C"
		elif color == 'dim-green':
			char = "D"
		elif color == 'green':
			char = "E"
		elif color == 'bright-green':
			char = "F"
		elif color == 'dim-orange':
			char = "G"
		elif color == 'orange':
			char = "H"
		elif color == 'bright-orange':
			char = "I"
		elif color == 'yellow':
			char = "J"
		elif color == 'lime':
			char = "K"
		elif color == 'inverted-red':
			char = "L"
		elif color == 'inverted-green':
			char = "M"
		elif color == 'inverted-orange':
			char = "N"
		elif color == 'red-on-green':
			char = "P"
		elif color == 'green-on-red':
			char = "Q"
		elif color == 'ryg':
			char = "R"
		elif color == 'rainbow':
			char = "S"
		else:
			char = "B"
		return "<C%c>" % char
	
	@classmethod
	def _get_graphic_tag(cls, page, block):
		# Optimize this for ease of use!
		return "<G%c%i>" % (page, block)
	
	@classmethod
	def _get_character_tag(cls, code):
		try:
			code = int(code)
		except (TypeError, ValueError):
			code = 0
		return "<U%02X>" % code
	
	@classmethod
	def _get_column_tag(cls, column):
		try:
			column = int(column)
		except (TypeError, ValueError):
			column = 0
		return "<N%02X>" % column
	
	@classmethod
	def _get_datetime_tag(cls, type):
		if type == 'date':
			char = "D"
		elif type == 'time':
			char = "T"
		else:
			char = "T"
		return "<K%c>" % char