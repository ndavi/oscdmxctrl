#!/usr/bin/python

###
# A simple DM512 controller application
#
# The OSCDMXCtrl class below incorporates an OSC-server & -client
# for controlling DMXCtrl over the network
###
# Stock, V2_Lab Rotterdam, Aug 2008
###

###
# Changelog
###
# version 0.1
#	initial version
###
# version 0.1.1
#	Implemented 'fade-lock' so that a new call to *DMXCtrl.fade*() interrupts/aborts a fade in-progress
#	Added *DMXCtrl.stopFade() method
###

from __future__ import with_statement

import optparse, os, sys, time, types, threading, warnings

import numpy

from xml.dom import minidom, DOMException, NotFoundErr
from xml.parsers import expat

import OSC

from dmxusbpro import *

global version
version = ("0.1.1", "r" + "$Rev: 5499 $"[6:-2])

class DMXCtrl(object):
	"""A simple DMX512 controller using the 'DMX USB Pro' box
	"""
	
	# DMX input & output buffers
	dmx_in = DMXPacket()
	dmx_out = DMXPacket()
	
	# scene-mempry (a list of DMXPackets)
	scene = []
		
	delay_factor = 0.95
		
	def __init__(self, serport='/dev/ttyUSB0', scenefile=None):
		"""Instantiate the DMXCtrl-object.
		This in turn instantiates a DMXUSBPro-object, connected to the provided serial-port
		Scenes can be loaded from disk, from an XML-file, if the filename is provded.
		"""
		self.box = DMXUSBPro(serport)
		
		self.fade_run = False
		self.fade_done = threading.Condition()
		
		if scenefile != None:
			self.loadScenes(scenefile)
		
	def __str__(self):
		return "%s v%s-%s" % (self.__class__.__name__, version[0], version[1])
	
	def close(self):
		"""Close the DMXCtrl
		Stop transmitting DMX-packets
		Close the DMXUSBPro-object's serial-port
		"""
		self.box.sendDMXPacketOnce(self.dmx_out)
		self.box.close()

	def sendDMX(self):
		"""Send the DMXPacket currently held in the output-buffer (self.dmx_out)
		to the DMXUSBPro box
		"""
		self.box.sendDMX(self.dmx_out)
		
	def receiveDMX(self):
		"""Receive a DMXPacket from the DMXUSBPro box,
		and store it in the input-buffer (self.dmx_in)
		"""
		self.dmx_in = self.box.receiveDMX()

	def setTXChannel(self, ch, val):
		"""Change the value of one channel (i.e. slot) in the currently held DMXPacket
		Send the changed DMXPacket to the DMXUSBPro box (see sendDMX())
		"""
		self.dmx_out.setSlot(ch, val)
		self.sendDMX()
		
	def getTXChannel(self, ch):
		"""Return the value of one channel (i.e. slot) of the DMXPacket
		currently held by the output-buffer (self.dmx_out)
		"""
		return self.dmx_out.getSlot(ch)

	def getRXChannel(self, ch):
		"""Return the value of one channel (i.e. slot) of the DMXPacket
		currently held by the input-buffer (self.dmx_in)
		"""
		return self.dmx_in.getSlot(ch)

	def fadeTXChannel(self, ch, val, duration=1):
		"""Fade given channel (i.e. slot) from its current value to the given value.
		'duration' sets the fade-duration in (floating-point) seconds.
		"""
		if self.fade_run:
			with self.fade_done:
				self.fade_run = False	# interrupt other fade-in-progress
				self.fade_done.wait()	# wait for interrupted fade to finish
		
		self.fade_run = True
		ret = False
		
		if (type(val) != types.IntType) or (val < 0) or (val > 255):
			raise ValueError("Invalid channel value: '%s'" % str(val))
		
		if ch > len(self.dmx_out):
			self.dmx_out.setSlot(ch, 0)
		
		from_val = self.getTXChannel(ch)
		
		steps = max(1, int(duration * self.box.params['dmx_rate']))
		delay = self.delay_factor / self.box.params['dmx_rate']
		
		if steps > 512:
			delay *= steps / 512.
			steps = 512
			
		for st in range(1, steps + 1):
			self.setTXChannel(ch, ((from_val * (steps - st)) + (val * st)) / steps)
			if not self.fade_run:		# we got interrupted
				break
			
			time.sleep(delay)
		else:			# fade completed without interruptions
			self.fade_run = False
			ret = True
		
		with self.fade_done:
			self.fade_done.notify()
		
		return ret
	
	def storeScene(self, nr):
		"""Store the currently held DMXPacket in the scene-memory at the indicated location
		"""
		if (type(nr) != types.IntType) or (nr < 0):
			raise ValueError("Invalid scene number '%s'" % str(nr))
		
		while nr >= len(self.scene):
			self.scene.append(None)
			
		self.scene[nr] = self.dmx_out.copy()

	def recallScene(self, nr):
		"""Recall the indicated scene from the scene-memory
		Send the recalled scene to the DMXUSBPro box (see sendDMX())
		"""
		if (type(nr) != types.IntType) or (nr < 0) or (nr >= len(self.scene)):
			raise ValueError("Invalid scene number '%s'" % str(nr))

		if self.scene[nr] == None:
			raise IndexError("Scene %d is empty" % nr)
		
		self.dmx_out = self.scene[nr].copy()
		self.sendDMX()
		
	def fadeScene(self, nr, duration=1):
		"""Cross-fade from the currently held DMXPacket (in self.dmx_out) to the indicated scene
		from scene-memory, in the given time.
		Send the new DMXPacket to the DMXUSBPro box after every step. (see sendDMX())
		This changes the DMXPacket held in the output-buffer (self.dmx_out). At the end of the fade-time,
		when this method returns, the output-buffer (self.dmx_out) is a copy of to the indicated scene.
		'duration' sets the cross-fade time in (floating-point) seconds
		"""
		if self.fade_run:
			with self.fade_done:
				self.fade_run = False	# interrupt other fade-in-progress
				self.fade_done.wait()	# wait for interrupted fade to finish
		
		self.fade_run = True
		ret = False
				
		if (type(nr) != types.IntType) or (nr < 0) or (nr >= len(self.scene)):
			raise ValueError("Invalid scene number '%s'" % str(nr))

		if self.scene[nr] == None:
			raise IndexError("Scene %d is empty" % nr)
		
		if (type(duration) != types.IntType) and (type(duration) != types.FloatType):
			raise TypeError("Duration must be int or float")
		
		dmx_to = self.scene[nr].copy()
	
		while len(self.dmx_out) < len(dmx_to):
			self.dmx_out.append(0)
			
		while len(self.dmx_out) > len(dmx_to):
			dmx_to.append(0)
			
		ar_from = numpy.array(self.dmx_out.getSlots(), dtype='int')
		ar_to = numpy.array(dmx_to.getSlots(), dtype='int')

		steps = max(1, int(duration * self.box.params['dmx_rate']))
		delay = self.delay_factor / self.box.params['dmx_rate']
		
		if steps > 512:
			delay *= steps / 512.
			steps = 512
		
		for st in range(1, steps + 1):
			ar_out = ((ar_from * (steps - st)) + (ar_to * st)) / steps
			self.dmx_out[1:] = ar_out.tolist()
			self.sendDMX()
			if not self.fade_run:	# interrupted
				break
			
			time.sleep(delay)
		else:
			self.fade_run = False
			ret = True
		
		with self.fade_done:
			self.fade_done.notify()
		
		return ret
	
	def stopFade(self):
		"""Interrupt a fade-in-progress
		"""
		if self.fade_run:
			with self.fade_done:
				self.fade_run = False
				self.fade_done.wait()
				
			return True
		
		return False
	
	def delScene(self, nr):
		"""Remove the given scene from the scene-memory.
		(This sets the scene-memory location to 'empty')
		"""
		if (type(nr) != types.IntType) or (nr < 0) or (nr >= len(self.scene)):
			raise ValueError("Invalid scene number '%s'" % str(nr))

		self.scene[nr] = None
	
	def _sceneToStr(self, nr):
		"""Return the given scene-memory slot as a multi-line string.
		The channel-values are represented by 2-digit Hexadecimal, 16 channels per row,
		preceded by a 3-digit Hexadeciaml slot-number.
		Upto 32 rows per scene (== 512 slots)
		"""
		out = ""
		
		if self.scene[nr] == None:
			return out
		
		values = self.scene[nr].getSlots()
		rows = ((len(values) - 1) // 16) + 1
		
		for row in range(rows):
			start = row * 16
			out += "%03X: " % (start + 1)
			for val in values[start:start+16]:
				out += "%02X " % val
		
			out += "\n"

		return out
			
	def _strToScene(self, nr, in_str):
		"""Parse the given multi-line string into a DMXPacket (see _sceneToStr(...))
		Store the new DMXPacket in the scene-memory at the indicarted location
		"""
		while nr >= len(self.scene):
			self.scene.append(None)
			
		scene = DMXPacket()
		
		for row in in_str.splitlines():
			for col in row.split():
				if not col.endswith(':'):
					try:
						val = int(col, 16)
					except ValueError:
						raise ValueError("Invalid channel value: '%s'" % str(col))
					
					scene.append(val)
					
		self.scene[nr] = scene
		
	def loadScenes(self, scenefile):
		"""Load the given XML-file and parse the scenes defined therein.
		Scene-definitions are stored in scene-memory (as DMXPackets)
		"""
		files_list = [scenefile]
		if not scenefile.endswith('.xml'):
			files_list.append("%s.xml" % scenefile)
			
		for f in files_list:
			self.scenefile = f
			if os.path.isfile(f):
				self.dom = minidom.parse(f)
				break
		else:
			warnings.warn("Scene-file '%s' not found." % scenefile)
			self.scenefile = files_list[-1]
			return
		
		scenes_nodes = self.dom.getElementsByTagName('DMXScenes')
		if not len(scenes_nodes):
			raise AttributeError("Element <DMXScenes>...</DMXScenes> missing from scenefile %s" % self.scenefile)
		
		for sc in scenes_nodes[0].getElementsByTagName('Scene'):
			nr_str = sc.getAttribute('nr')
			if not len(nr_str):
				raise AttributeError("Attribute 'nr' missing from XML scene definition")
			
			try:
				nr = int(nr_str)
			except ValueError:
				raise ValueError("Invalid 'nr' Attribute in XML scene definition: '%s'" % nr_str)
			
			tn = sc.firstChild
			
			if tn == None:
				raise AttributeError("DMX data missing from XML scene %d definition" % nr)
			
			if tn.nodeType != tn.TEXT_NODE:
				raise AttributeError("Wrong DMX data node-type (%d) in XML scene %d definition" % (tn.nodeType, nr))
			
			self._strToScene(nr, tn.data)
			
	def saveScenes(self, scenefile=None):
		"""Store the DMXPackets currently in the scene-memory in an XML-file
		If the scenefile name is not given, the filename from which the scenes were last loaded is used.
		"""
		self.dom = minidom.parseString("<DMXScenes></DMXScenes>")
		
		for nr in range(len(self.scene)):
			if self.scene[nr] == None:
				continue
			
			sc = self.dom.createElement('Scene')
			at = self.dom.createAttribute('nr')
			sc.setAttributeNode(at)
			sc.setAttribute('nr', str(nr))
			tn = self.dom.createTextNode(self._sceneToStr(nr))
			sc.appendChild(tn)
			self.dom.firstChild.appendChild(sc)
			
		if scenefile != None:
			if not scenefile.endswith('.xml'):
				scenefile += ".xml"
			self.scenefile = scenefile
			
		sf = open(self.scenefile, 'w')
		
		for line in self.dom.toprettyxml().splitlines():
			if not len(line):
				continue
			
			if (':' in line) and not (line.startswith('\t')):
				line = "\t\t" + line
			
			sf.write("%s\n" % line)
			
		sf.close()
		

class OSCDMXCtrl(DMXCtrl):
	"""An OSC-controlled version of the DMX Controller
	"""
	def __init__(self, serport='/dev/ttyUSB0', scenefile=None, listenurl=':6788'):
		"""Instantiate DMXCtrl, instantiate OSCMultiClient & ThreadingOSCServer
		"""
		super(self.__class__, self).__init__(serport, scenefile)
		
		# parse 'listenurl' argument
		(addr, server_prefix) = OSC.parseUrlStr(listenurl)
		if addr != None and addr[0] != None:
			if addr[1] != None:
					listen_address = addr
			else:
					listen_address = (addr[0], default_port)
		else:
			listen_address = ('', default_port)
		
		# Create OSC Client & Server
		self.cli = OSC.OSCMultiClient()
		self.srv = OSC.ThreadingOSCServer(listen_address, self.cli)
		self.srv.addDefaultHandlers(server_prefix)
		self.srv.setSrvInfoPrefix("/serverinfo")
		
		# Register DMX-specific message-handlers
		self.srv.addMsgHandler(server_prefix + "/dmx/scene", self.dmxSceneHandler)
		self.srv.addMsgHandler(server_prefix + "/dmx/channel", self.dmxChanHandler)
			
		self.srv_thread = None
	
	def start(self):
		"""Start the ThreadingOSCServer
		"""
		# create OSCServer's main thread
		self.srv_thread = threading.Thread(target=self.srv.serve_forever)
		self.srv_thread.start()
	
	def close(self):
		"""Stop the OSCServer threads
		Close the DMXUSBPro box' serial-port
		"""
		self.srv.close()
		# wait for OSCServer to finish
		if isinstance(self.srv_thread, threading.Thread) and self.srv_thread.isAlive():
			self.srv_thread.join()
		
		# close DMXCtrl
		super(self.__class__, self).close()
	
	###
	# OSC Message-handlers (& support) 
	###
	
	def _lsOSCScenes(self):
		"""Construct an OSCBundle listing all exisiting scene-numbers
		"""
		reply = OSC.OSCBundle('/dmxinfo')
		for nr in range(len(self.scene)):
			if self.scene[nr] == None:
				continue
			
			reply.append(('scene', nr))
		
		return reply
		
	def _sendOSCScene(self, dmx_pkt, from_ch, to_ch, client_address):
		"""Construct an OSCBundle listing the given (range of) channel(s) and their values
		"""
		if (from_ch < 1) or (from_ch > dmx_pkt.packetMaxSlots):
			self.srv.reportErr("Invalid channel-number in OSC /dmx/scene 'get ...' command: '%d'" % from_ch, client_address)
		if (to_ch < 1)or (to_ch < from_ch)  or (to_ch > dmx_pkt.packetMaxSlots):
			self.srv.reportErr("Invalid channel-number in OSC /dmx/scene 'get ...' command: '%d'" % to_ch, client_address)
		
		reply = OSC.OSCBundle('/dmxinfo')
		for ch in range(from_ch, to_ch + 1):
			if ch > len(dmx_pkt):
				break
			
			reply.append(('channel', ch, dmx_pkt.getSlot(ch)))
			
		if len(reply):
			return reply
		
		return None
		
	def dmxSceneHandler(self, addr, tags, data, client_address):
		"""Handle OSC-messages to the '.../dmx/scene' address
		"""
		if not len(data):
			return None
		
		if data[0] in ('help', 'info'):	# handler-info request
			reply = OSC.OSCBundle(self.srv.info_prefix)
			reply.append(("server", str(self.srv)))
			reply.append(("scene_command", "ls | list : list scenes in scene-memory"))
			reply.append(("scene_command", "<sc> : recall scene"))
			reply.append(("scene_command", "<sc> <time> : fade to scene"))
			reply.append(("scene_command", "stop : abort a fade in progress"))
			reply.append(("scene_command", "store <sc> : store current scene"))
			reply.append(("scene_command", "get <sc> : return all channels' values from scene"))
			reply.append(("scene_command", "get <sc> <ch> : return a channel's value from scene"))
			reply.append(("scene_command", "get <sc> <from_ch> <to_ch> : return a range of channels' values from scene"))
			reply.append(("scene_command", "load [<file>] : load scenes from file"))
			reply.append(("scene_command", "save [<file>] : save scenes to file"))
			return reply
	
		if data[0] in ('ls', 'list'):
			return self._lsOSCScenes()
		
		if data[0] == 'stop':
			reply = OSC.OSCMessage('/dmxinfo')
			reply.append(['scene', 'fade', 'done'])
			if self.stopFade():
				return reply
			
			return None
				
		if data[0] == 'store':
			if len(data) < 2:
				self.srv.reportErr("Missing scene-number in OSC /dmx/scene 'store ...' command", client_address)
				return None
		
			sc = data.pop(1)
			try:
				self.storeScene(sc)
			except ValueError, e:
				self.srv.reportErr("Unrecognzed scene-number in OSC /dmx/scene 'store ...' command: %s" % str(e), client_address)
			
			return None
	
		if data[0] == 'load':
			if len(data) < 2:
				filename = self.scenefile
			else:
				filename = data.pop(1)
				if type(filename) not in types.StringTypes:
					self.srv.reportErr("Filename in OSC /dmx/scene 'load ...' command must be a string", client_address)
					return None
				
			try:
				self.loadScenes(filename)
			except Exception, e:
				self.srv.reportErr("Error loading scenes: %s" % str(e), client_address)
			
			return self._lsOSCScenes()
				
		if data[0] == 'save':
			if len(data) < 2:
				filename = None
			else:
				filename = data.pop(1)
				if type(filename) not in types.StringTypes:
					self.srv.reportErr("Filename in OSC /dmx/scene 'save ...' command must be a string", client_address)
					return None
				
			try:
				self.saveScenes(filename)
			except Exception, e:
				self.srv.reportErr("Error saving scenes: %s" % str(e), client_address)
			
			reply = OSC.OSCMessage(self.srv.info_prefix)
			reply.append("saved scenes to '%s'" % self.scenefile)
			
			return reply
				
		if data[0] == 'get':
			del data [0]
			if not len(data):
				self.srv.reportErr("Missing scene-number in OSC /dmx/scene 'get ...' command", client_address)
				return None
			
			nr = data.pop(0)
			if type(nr) != types.IntType:
				self.srv.reportErr("Unrecognzed scene-number in OSC /dmx/scene 'get ...' command: '%s'" % nr, client_address)
				return None
			
			if (nr < 0) or (nr >= len(self.scene)):
				self.srv.reportErr("Invalid scene-number in OSC /dmx/scene 'get ...' command: %d" % nr, client_address)
				return None
			
			scene = self.scene[nr]
			if scene == None:
				self.srv.reportErr("Scene %d is empty" % nr, client_address)
			
			if not len(data):	# get all channels
				return self._sendOSCScene(scene, 1, scene.packetMaxSlots, client_address)
		
			ch = data.pop(0)
			if type(ch) != types.IntType:
				self.srv.reportErr("Unrecognzed scene-number in OSC /dmx/scene 'get ...' command: '%s'" % ch, client_address)
				return None
			
			if not len(data):	# get one channel
				return self._sendOSCScene(scene, ch, ch, client_address)
		
			to_ch = data.pop(0)
			if type(to_ch) != types.IntType:
				self.srv.reportErr("Unrecognzed scene-number in OSC /dmx/scene 'get ...' command: '%s'" % to_ch, client_address)
				return None
			
			return self._sendOSCScene(scene, ch, to_ch, client_address)
		
		if type(data[0]) != types.IntType:
			self.srv.reportErr("Unrecognzed scene-number in OSC /dmx/scene command: '%s'" % data[0], client_address)
			return None
		
		sc = data.pop(0)
		if not len(data):	# recall scene request
			try:
				self.recallScene(sc)
			except IndexError, e:
				self.srv.reportErr(str(e), client_address)
			except ValueError, e:
				self.srv.reportErr("Invalid scene-number in OSC /dmx/scene command: %s" % str(e), client_address)
			
			return None
			
		duration = data.pop(0)
		if type(duration) not in (types.IntType, types.FloatType):
			self.srv.reportErr("Unrecognized fade-time in OSC /dmx/scene command: '%s'" % str(duration), client_address)
			return None
		
		if duration < 0:
			self.srv.reportErr("Invalid fade-time in OSC /dmx/scene command: '%.2f'" % duration, client_address)
			return None
			
		reply = OSC.OSCMessage('/dmxinfo')
		reply.append(['scene', 'fade', 'done'])
			
		try:
			if self.fadeScene(sc, duration):
				return reply
		except IndexError, e:
			self.srv.reportErr(str(e), client_address)
		except ValueError, e:
			self.srv.reportErr("Invalid scene-number in OSC /dmx/scene command: %s" % str(e), client_address)
			
		return None
		
	def _sendOSCChannels(self, from_ch, to_ch, client_address):
		"""Construct an OSCBundle listing the given (range of) channel(s) and their values
		"""
		if (from_ch < 1) or (from_ch > self.dmx_out.packetMaxSlots):
			self.srv.reportErr("Invalid channel-number in OSC /dmx/channel '[get] ...' command: '%d'" % from_ch, client_address)
		if (to_ch < 1)or (to_ch < from_ch)  or (to_ch > self.dmx_out.packetMaxSlots):
			self.srv.reportErr("Invalid channel-number in OSC /dmx/channel '[get] ...' command: '%d'" % to_ch, client_address)
		
		reply = OSC.OSCBundle('/dmxinfo')
		for ch in range(from_ch, to_ch + 1):
			if ch > len(self.dmx_out):
				break
			
			reply.append(('channel', ch, self.getTXChannel(ch)))
			
		if len(reply):
			return reply
		
		return None
		
	def dmxChanHandler(self, addr, tags, data, client_address):
		"""Handle OSC-messages to the '.../dmx/channel' address
		"""
		if not len(data):
			return None
		
		if data[0] in ('help', 'info'):	# handler-info request
			reply = OSC.OSCBundle(self.srv.info_prefix)
			reply.append(("server", str(self.srv)))
			reply.append(("channel_command", "get : return all channels' current value"))
			reply.append(("channel_command", "[get] <ch> : return a channel's current value"))
			reply.append(("channel_command", "get <from_ch> <to_ch> : return range of channels' current value"))
			reply.append(("channel_command", "[set] <ch> <val> : set a channel to value"))
			reply.append(("channel_command", "[set] <ch> <val> <time> : fade a channel to value"))
			reply.append(("channel_command", "stop : abort a fade in progress"))
			return reply
		
		if data[0] == 'stop':
			reply = OSC.OSCMessage('/dmxinfo')
			reply.append(['channel', 'fade', 'done'])
			if self.stopFade():
				return reply
			
			return None
				
		if data[0] == 'get':
			del data[0]
		
			if not len(data):	# get all channels
				return self._sendOSCChannels(1, self.dmx_out.packetMaxSlots, client_address)
		
			ch = data.pop(0)
			if type(ch) != types.IntType:
				self.srv.reportErr("Unrecognzed channel-number in OSC /dmx/channel command: '%s'" % ch, client_address)
				return None
			
			if not len(data):	# get one channel
				return self._sendOSCChannels(ch, ch, client_address)
			
			to_ch = data.pop(0)
			if type(to_ch) != types.IntType:
				self.srv.reportErr("Unrecognzed channel-number in OSC /dmx/channel command: '%s'" % to_ch, client_address)
				return None
			
			return self._sendOSCChannels(ch, to_ch, client_address)
		
		if data[0] == 'set':
			if len(data) > 2:
				del data[0]
			else:
				self.srv.reportErr("Missing channel value in OSC /dmx/channel 'set ...' command", client_address)
				return None
		
		ch = data.pop(0)
		if type(ch) != types.IntType:
			self.srv.reportErr("Unrecognzed channel-number in OSC /dmx/channel command: '%s'" % ch, client_address)
			return None
		
		if not len(data):	# get channel value request
			return self._sendOSCChannels(ch, ch, client_address)
		
		val = data.pop(0)
		if type(val) != types.IntType:
			self.srv.reportErr("Unrecognzed channel value in OSC /dmx/channel '[set] ...' command: '%s'" % val, client_address)
			return None
		
		if not len(data):	# set channel value request
			try:
				self.setTXChannel(ch, val)
			except IndexError, e:
				self.srv.reportErr("Invalid channel-number in OSC /dmx/channel '[set] ...' command: %s" % str(e), client_address)
			except struct.error, e:
				self.srv.reportErr("Invalid channel value in OSC /dmx/channel '[set] ...' command: %s" % str(e), client_address)
			return None
		
		duration = data.pop(0)
		if type(duration) not in (types.IntType, types.FloatType):
			self.srv.reportErr("Unrecognized fade-time in OSC /dmx/channel '[set] ...' command: '%s'" % str(duration), client_address)
			return None
		
		if duration < 0:
			self.srv.reportErr("Invalid fade-time in OSC /dmx/channel '[set] ...' command: '%.2f'" % duration, client_address)
			return None
			
		reply = OSC.OSCMessage('/dmxinfo')
		reply.append(['channel', 'fade', 'done'])
			
		try:
			if self.fadeTXChannel(ch, val, duration):
				return reply
		except IndexError, e:
			self.srv.reportErr("Invalid channel-number in OSC /dmx/channel '[set] ...' command: %s" % str(e), client_address)
		except struct.error, e:
			self.srv.reportErr("Invalid channel value in OSC /dmx/channel '[set] ...' command: %s" % str(e), client_address)
			
		return None

###
# Main 
###
# Creates and starts an OSCDMXCtrl instance
###

if __name__ == '__main__':
	# Define default values
	default_serport = "/dev/ttyUSB0"
	default_port = 6788
	default_listen = ":%d" % default_port
	default_scenefile = "scenes.xml"

	op = optparse.OptionParser()

	# Define command-line options and arguments
	op.add_option("-s", "--serport", action='store', type='string', dest='serport', metavar='DEV',
									help="connect to DMX USB Pro box on DEV [default = %s]" % default_serport)
	op.add_option("-l", "--listen", action='store', type='string', dest='listen', metavar='URL',
									help="listen for OSC-messages on URL [default = %s]" % default_listen)
	op.add_option("-f", "--scenefile", action='store', type='string', dest='scenefile', metavar='FILE',
									help="load scene-memory from FILE [default = %s]" % default_scenefile)

	# Set defaults
	op.set_defaults(serport=default_serport)
	op.set_defaults(listen=default_listen)
	op.set_defaults(scenefile=default_scenefile)

	# Parse command-line options
	(opts, args) = op.parse_args()

	def showwarning(message, category, filename, lineno, file=None):
		"""Alternate 'warnings' printing function.
		Writes warnings to stderr (using the write() method)
		"""
		sys.stderr.write("Warning: %s\n" % message)
	
	warnings.showwarning = showwarning
	
	# Instatitiate (and connect to) OSC DMX USB Pro interface
	try:
		#dc = DMXCtrl(opts.serport, opts.scenefile)
		odc = OSCDMXCtrl(opts.serport, opts.scenefile, opts.listen)
		
	except DMXUSBError, e:
		sys.stderr.write("DMXUSBError: USB DMX Pro not detected on '%s': %s\n" % (opts.serport, str(e)))
		sys.exit(1)
	
	except serial.SerialException, e:
		sys.stderr.write("SerialException: %s\n" % str(e))
		sys.exit(2)

	sys.stdout.write("%s\n" % str(odc))
	sys.stdout.write("Detected %s\n" % str(odc.box))
	sys.stdout.write("Starting %s\n" % str(odc.srv))
	
	# start OSCServer thread
	odc.start()
	
	sys.stdout.write("Use Ctrl-C to quit\n")
	
	# main loop
	try:
		while True:
			time.sleep(1)

	except KeyboardInterrupt:
		sys.stdout.write("\nQuitting!\n")

	odc.close()
	
	
