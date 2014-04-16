#!/usr/bin/env python
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
EXAMPLE SCRIPT: Interactive shell for AM03127-based LED signs
"""

import argparse
import cmd
import ledsign

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
	
	def do_page(self, command):
		cmdparts = command.split()
		page = cmdparts[0]
		text = " ".join(cmdparts[1:])
		
		content = ledsign.am03127.PageContentBBCodeParser().render(text)
		
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
	
	def do_p(self, command):
		# p = page a
		return self.do_page("A %s" % command)
	
	def do_pn(self, command):
		# pn = page a, narrow
		return self.do_page("A [font=narrow]%s" % command)
	
	def do_pb(self, command):
		# pb = page a, bold
		return self.do_page("A [font=bold]%s" % command)

def main():
	parser = argparse.ArgumentParser(description = "Interactive AM03127 LED sign shell")
	parser.add_argument('-d', '--device',
		default = "/dev/ttyUSB0",
		help = "Serial device to use")
	
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
	
	sign = ledsign.am03127.LEDSign(
		port = args.device,
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
		shell.cmdloop()
	except KeyboardInterrupt:
		print

if __name__ == "__main__":
	main()