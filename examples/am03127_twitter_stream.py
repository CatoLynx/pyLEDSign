#!/usr/bin/env python
# Copyright (C) 2014 Julian Metzler
# See the LICENSE file for the full license.

"""
EXAMPLE SCRIPT: Stream tweets to the LED sign
Requires the TweetPony library, which can be installed with pip, or found at https://github.com/Mezgrman/TweetPony
"""

import argparse
import json
import ledsign
import re
import tweetpony

def main():
	parser = argparse.ArgumentParser(description = "Tweet streamer for AM03127 LED sign")
	
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
	
	parser.add_argument('-p', '--page',
		choices = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'),
		default = 'A',
		help = "The page to send the tweets to")
	
	parser.add_argument('-s', '--speed',
		choices = ('slowest', 'slow', 'medium', 'fast'),
		default = 'fast',
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
		default = 'scroll_down',
		help = "Lagging effect")
	
	parser.add_argument('-tf', '--token-file',
		type = str,
		default = "twitter_tokens.json",
		help = "A JSON file containing the Twitter API tokens (see source code for key names)")
	
	parser.add_argument('-bf', '--blacklist-file',
		type = str,
		default = "twitter_blacklist.json",
		help = "A JSON file containing the blacklisted stuff (see source code for key names)")
	
	parser.add_argument('-k', '--keywords',
		type = str,
		required = True,
		help = "A comma-separated list of tweet keywords to stream")
	
	args = parser.parse_args()
	
	with open(args.token_file, 'r') as f:
		keys = json.load(f)
	
	with open(args.blacklist_file, 'r') as f:
		blacklist = json.load(f)
	
	sign = ledsign.am03127.LEDSign(
		port = args.device,
		baudrate = args.baudrate,
		timeout = None,
		id = args.id
	)
	
	# Set the page to run
	sign.send_schedule(
		schedule = "A",
		pages = args.page
	)

	settings = {
		'speed': getattr(sign, "SPEED_%s" % args.speed.upper()),
		'method': getattr(sign, "METHOD_%s" % args.method.upper()),
		'wait': args.wait,
		'lead': getattr(sign, "EFFECT_%s" % args.lead.upper()),
		'lag': getattr(sign, "EFFECT_%s" % args.lag.upper())
	}
	
	message_parser = ledsign.am03127.parsers.PageContentBBCodeParser()
	
	class LEDSignStreamProcessor(tweetpony.StreamProcessor):
		def on_status(self, status):
			# Ignore replies and retweets and apply the blacklists
			if status.text.startswith("@") or hasattr(status, 'retweeted_status') or "RT @" in status.text:
				return True
			
			for word in blacklist['words']:
				if word.lower() in status.clean_text().lower():
					return True
			
			for client in blacklist['clients']:
				if status.source.lower() == client.lower():
					return True
			
			for user in blacklist['users']:
				if status.user.screen_name.lower() == user.lower():
					return True
			
			text = re.sub(r"(#.+?)(?=\s|$)", "[color=green]\\1[color=orange]", status.clean_text().replace("\n", " ")) # Color hashtags green
			content = message_parser.render("[color=red]@%s: [color=orange]%s" % (status.user.screen_name, text)).render()
			
			success = sign.send_page(
				page = args.page,
				lead = settings['lead'],
				speed = settings['speed'],
				method = settings['method'],
				wait = settings['wait'],
				lag = settings['lag'],
				content = content.encode('utf-8')
			)
			success_str = " OK " if success else "FAIL"
			
			print "[%s] %s %s" % (success_str, status.user.screen_name.ljust(15), status.clean_text().replace("\n", " "))
			return True
	
	api = tweetpony.API(keys['consumer_key'], keys['consumer_secret'], keys['access_token'], keys['access_token_secret'])
	processor = LEDSignStreamProcessor(api)
	
	try:
		api.filter_stream(track = args.keywords, processor = processor)
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()