#!/usr/bin/env python
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
EXAMPLE SCRIPT: Interactive shell for AM03127-based LED signs
"""

import argparse
import cmd
import ledsign
import os
import traceback

from serial import SerialException

class InteractiveShell(cmd.Cmd):
	"""
	The "interpreter" for the LED sign shell
	"""
	
	prompt = ">>> "
	
	def do_pages(self, pages):
		success = self.sign.send_schedule(
			schedule = "A",
			pages = pages
		)
		print "Pages set!" if success else "Failed to set pages"
	
	def help_pages(self):
		print "Link the pages to run. Syntax: pages <PAGENO><PAGENO><PAGENO> etc."
	
	def do_page(self, command):
		cmdparts = command.split()
		page = cmdparts[0]
		text = " ".join(cmdparts[1:])
		
		content = ledsign.am03127.PageContentBBCodeParser().render(text)
		
		try:
			success = self.sign.send_page(
				page = page,
				lead = self.settings['lead'],
				speed = self.settings['speed'],
				method = self.settings['method'],
				wait = self.settings['wait'],
				lag = self.settings['lag'],
				content = content
			)
		except SerialException:
			# Probably just an I/O Error, try with a different device name
			
			try:
				device = _get_device_name()
			except Exception as e:
				print e
				success = False
			else:
				print "Device error, trying %s" % device
				self.sign = ledsign.am03127.LEDSign(
					port = device,
					baudrate = self.sign.baudrate,
					timeout = self.sign.timeout,
					id = self.sign.id
				)
				
				success = self.sign.send_page(
					page = page,
					lead = self.settings['lead'],
					speed = self.settings['speed'],
					method = self.settings['method'],
					wait = self.settings['wait'],
					lag = self.settings['lag'],
					content = content
				)
		
		print "Page sent!" if success else "Failed to send page"
	
	def help_page(self):
		print "Send a message to the sign. Syntax: page <PAGENO> <MESSAGE>"
	
	def do_p(self, command):
		# p = page a
		return self.do_page("A %s" % command)
	
	def help_p(self):
		print "Shortcut for page A"
	
	def do_pn(self, command):
		# pn = page a, narrow
		return self.do_page("A [font=narrow]%s" % command)
	
	def help_pn(self):
		print "Shortcut for page A [font=narrow]"
	
	def do_pb(self, command):
		# pb = page a, bold
		return self.do_page("A [font=bold]%s" % command)
	
	def help_pb(self):
		print "Shortcut for page A [font=bold]"
	
	def do_lead(self, lead):
		self.settings['lead'] = getattr(self.sign, "EFFECT_%s" % lead.upper())
	
	def help_lead(self):
		print "Set the leading effect. Can be immediate, xopen, curtain_up, curtain_down, scroll_left, scroll_right, vopen, vclose, scroll_up, scroll_down, hold, snow, twinkle, block_move, random, hello_world, welcome or amplus."
	
	def do_lag(self, lag):
		self.settings['lag'] = getattr(self.sign, "EFFECT_%s" % lag.upper())
	
	def help_lag(self):
		print "Set the lagging effect. Can be immediate, xopen, curtain_up, curtain_down, scroll_left, scroll_right, vopen, vclose, scroll_up, scroll_down or hold."
	
	def do_wait(self, duration):
		self.settings['wait'] = float(duration)
	
	def help_wait(self):
		print "Set the waiting time. Value between 0.5 and 25 seconds."
	
	def do_method(self, method):
		self.settings['method'] = getattr(self.sign, "METHOD_%s" % method.upper())
	
	def help_method(self):
		print "Set the display effect. Can be normal, blinking, song_1, song_2 or song_3."
	
	def do_speed(self, speed):
		self.settings['speed'] = getattr(self.sign, "SPEED_%s" % speed.upper())
	
	def help_speed(self):
		print "Set the effect speed. Can be fast, medium, slow or slowest."

def _get_device_name():
	# Look for USB to RS232 converters (rather dirty and specific solution)
	
	devices = os.listdir("/dev")
	candidates = [device for device in devices if device.startswith("ttyUSB")]
	if len(candidates) == 0:
		raise Exception("No serial devices found.")
	return "/dev/" + candidates[0]

def main():
	parser = argparse.ArgumentParser(description = "Interactive AM03127 LED sign shell")
	
	"""parser.add_argument('-d', '--device',
		default = "/dev/ttyUSB0",
		help = "Serial device to use")"""
	
	parser.add_argument('-b', '--baudrate',
		type = int,
		choices = (1200, 2400, 4800, 9600, 19200),
		default = 9600,
		help = "Baudrate for the serial port")
	
	parser.add_argument('-i', '--id',
		type = int,
		default = 1,
		help = "ID of the LED sign")
	
	parser.add_argument('-s', '--speed',
		choices = ('slowest', 'slow', 'medium', 'fast'),
		default = 'medium',
		help = "Effect speed")
	
	parser.add_argument('-m', '--method',
		choices = ('normal', 'blinking', 'song_1', 'song_2', 'song_3'),
		default = 'normal',
		help = "Display effect while waiting")
	
	parser.add_argument('-w', '--wait',
		type = float,
		default = 2.0,
		help = "Time to show the text until it disappears")
	
	parser.add_argument('-lead', '--lead',
		choices = ('immediate', 'xopen', 'curtain_up', 'curtain_down', 'scroll_left', 'scroll_right', 'vopen', 'vclose', 'scroll_up', 'scroll_down', 'hold', 'snow', 'twinkle', 'block_move', 'random', 'hello_world', 'welcome', 'amplus'),
		default = 'scroll_left',
		help = "Leading effect")
	
	parser.add_argument('-lag', '--lag',
		choices = ('immediate', 'xopen', 'curtain_up', 'curtain_down', 'scroll_left', 'scroll_right', 'vopen', 'vclose', 'scroll_up', 'scroll_down', 'hold'),
		default = 'scroll_left',
		help = "Lagging effect")
	
	args = parser.parse_args()
	
	device = _get_device_name()
	
	sign = ledsign.am03127.LEDSign(
		port = device,
		baudrate = args.baudrate,
		timeout = None,
		id = args.id
	)
	
	settings = {
		'speed': getattr(sign, "SPEED_%s" % args.speed.upper()),
		'method': getattr(sign, "METHOD_%s" % args.method.upper()),
		'wait': args.wait,
		'lead': getattr(sign, "EFFECT_%s" % args.lead.upper()),
		'lag': getattr(sign, "EFFECT_%s" % args.lag.upper())
	}
	
	shell = InteractiveShell()
	shell.sign = sign
	shell.settings = settings
	
	try:
		while True:
			try:
				shell.cmdloop()
			except KeyboardInterrupt:
				raise
			except:
				traceback.print_exc()
	except KeyboardInterrupt:
		print

if __name__ == "__main__":
	main()