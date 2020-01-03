from frontend import alarm_models
import os
from datetime import datetime
from rpi_ws281x import Color

class alarmclock:

	def __init__(self, sound, spotify, radio, strip, clock):
		self.sound = sound
		self.spotify = spotify
		self.radio = radio
		self.strip = strip
		self.clock = clock
		self.reload_xml()

	def reload_xml(self):
		print('[alarm] Loading alarm list')
		# Load alarms from XML
		bindir = os.path.dirname(os.path.realpath(__file__))
		self.alarms = alarm_models.load_alarm_list(bindir + '/../config/alarms.xml')
	
	def snooze_short(self):
		# Go through all alarms
		for alarm in self.alarms:
			# Check alarm is ON
			if alarm.status == 'on' or alarm.status == 'snooze_on':
				# Go silent
				self.radio.kill_radio()
				self.spotify.kill_spotify()
				if alarm.snooze.enable:
					print('[alarm] Alarm ' + alarm.name + ' going to snooze wait mode')
					alarm.status = 'snooze_wait'
					# Calculate Snooze time
					now = datetime.now()
					alarm.snooze_hh = now.hour
					alarm.snooze_mm = now.minute + alarm.snooze.time
					if alarm.snooze_mm > 59:
						alarm.snooze_mm -= 60
						alarm.snooze_hh += 1
						if alarm.snooze_hh > 23:
							alarm.snooze_hh -= 24
				else:
					print('[alarm] Alarm ' + alarm.name + ' going off')
					alarm.status = 'off'

	def snooze_long(self):
		# Go through all alarms
		for alarm in self.alarms:
			# Check alarm is ON or in SNOOZE wait
			if alarm.status == 'on' or alarm.status == 'snooze_on' or alarm.status == 'snooze_wait':
				# Go silent
				self.radio.kill_radio()
				self.spotify.kill_spotify()
				print('[alarm] Alarm ' + alarm.name + ' going off')
				alarm.status = 'off'
				self.sound.play('off')
				# Put light OFF		
				self.strip.colorWipe(Color(0, 0, 0))

	def play(self, alarm):
		# Determine source
		if alarm.source.type=='spotify':
			print('[alarm] Alarm ' + alarm.name + ' triggered! (spotify)')
			# Kill previous playbacks if exist
			self.radio.kill_radio()
			self.spotify.kill_spotify()
			self.spotify.play_URI(URI=alarm.source.item, shuffle=alarm.source.randomize)
		elif alarm.source.type=='radio':
			print('[alarm] Alarm ' + alarm.name + ' triggered! (radio)')
			# Kill previous playbacks if exist
			self.radio.kill_radio()
			self.spotify.kill_spotify()
			self.radio.tune_freq(freq=alarm.source.item)
		
		# Put light ON		
		self.strip.colorWipe(Color(30, 5, 0))

	def run(self):
		now = datetime.now()
		hh = now.hour
		mm = now.minute
		wd = now.weekday()
		# Go through all alarms
		for alarm in self.alarms:
			# Check alarm is enabled
			if alarm.periodic.enable:
				# Check alarm has not been trigered yet
				if alarm.status == 'idle':
					# Check current weekday is enabled in alarm
					if alarm.periodic.weekday[wd]:
						# Check current time is alarm time
						if alarm.hour == hh and alarm.minute == mm:
							# Trigger alarm
							alarm.status = 'on'
							self.play(alarm)
				# Check if alarm is in snooze
				elif alarm.status == 'snooze_wait':
					# Check current time is snooze time
					if alarm.snooze_hh == hh and alarm.snooze_mm == mm:
						# Trigger alarm
						print('[alarm] Alarm ' + alarm.name + ' going to snooze on mode')
						alarm.status = 'snooze_on'
						self.play(alarm)
				# Check if alarm is in off
				elif alarm.status == 'off':
					# Check current time is alarm time
					if alarm.hour == hh and alarm.minute == mm:
						# Wait until current time has changed
						pass
					else:
						# Go to idle again
						print('[alarm] Alarm ' + alarm.name + ' going to idle')
						alarm.status = 'idle'
					