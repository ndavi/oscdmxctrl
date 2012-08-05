#!/usr/bin/python

###
# 'DMX USB Pro' classes
###
# A set of classes for communicating with an Enttec 'DMX USB Pro' box
# http://www.enttec.com/index.php?main_menu=Products&prod=70304&show=description&name=dmxusbpro
#
# This code is designed for (and tested against) the 'DMX USB Pro' firmware v1.44
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
#	Added DMXUSBPro.setTimeout() method
###

import string, struct, time, types, os
import serial

from dmx512 import *

class DMXUSBError(BaseException):
	pass


global DMXUSBLabels
DMXUSBLabels = {   0:'NONE',
				   1:'PROG_FIRMW_REQ',
				   2:'PROG_FLASH_PAGE',
				   3:'GET_WIDGET_PARAMS',
				   4:'SET_WIDGET_PARAMS',
				   5:'RX_DMX',
				   6:'TX_DMX_ONLY',
				   7:'TX_DMX_RX_DMX',
				   8:'DMX_RX_ON_CHG_REQ',
				   9:'RX_DMX_CHG',
				  10:'GET_WIDGET_SERIAL',
				  11:'TX_RDM_DISC',
				0x7E:'SOM',
				0xE7:'EOM',
				0xFF:'INVALID'
				}
				
global DMXUSBCodes
DMXUSBCodes = dict(zip(DMXUSBLabels.values(), DMXUSBLabels.keys()))


###
# Generic DMXUSB Packet 
###

class DMXUSBPacket(object):
	"""Class to build or decode data-packets for / from the 'USB DMX Pro' box
	"""
	
	packetMaxData = 514
	
	TX_Fields = [('data', packetMaxData, 'B')]
	RX_Fields = TX_Fields
	
	def __init__(self, label=None, data=None):
		"""Set-up a new DMXUSBPacket.
		The DMXUSBPacket's label (i.e. type) may be provided. If no label is provided, it defaults to '0',
		which is NOT a valid 'USB DMX Pro' message-type. A valid label must be set before the packet is sent.
		(see DMXUSBPacket.setLabel(...) for a list of valid label values)
		"""
		if label == None:
			label = 0
		elif label in DMXUSBCodes:
			label = DMXUSBCodes[label]
		elif label not in DMXUSBLabels:
			raise DMXUSBError("Invalid label: '%s'" % str(label))
		
		in_str = struct.pack('<BBHB', DMXUSBCodes['SOM'], label, 0, DMXUSBCodes['EOM'])
		self.fromString(in_str)
		
		if data != None:
			self.setData(data)
	
	def __str__(self):
		"""Return the DMXUSBPacket as a string
		"""
		return string.join(self.data, '')
	
	def __len__(self):
		"""Return the number of data-bytes in the DMXUSBPacket
		"""
		return (len(self.data) - 5)
	
	def __repr__(self):
		"""Return the DMXUSBPacket as a human-readable string
		"""
		bytes = str(self)
		label = struct.unpack('B', bytes[1])[0]
		size = struct.unpack('<H', bytes[2:4])[0]
		out = "<DMXUSBPacket %s [%d]: " % (DMXUSBLabels[label], size)
		if len(self):
			fmt = 'B' * len(self)
			out += str(struct.unpack(fmt, bytes[4:-1]))
		out += ">"
		return out
		
	def fromString(self, in_str):
		"""Parse the given string into the DMXUSBPacket. 
		The 1st char of the string should be the SOM (Start Of Message) byte 0x7E (126),
		the 2nd char sets the label (i.e. type) of the DMXUSBPacket (see DMXUSBPacket.setLabel(...))
		the 3rd & 4th char encode the data-block length (LSB & MSB, i.e. Little-Endian)
		then follows the optional data-block,
		and the last char of the string should be the EOM (End Of Message) byte 0xE7 (231),
		"""
		if not ((type(in_str) in types.StringTypes) and (len(in_str) >= 5)):
			return
		
		som = struct.unpack('B', str(in_str)[0])[0]
		if som != DMXUSBCodes['SOM']:
			raise DMXUSBError("String has invalid SOM byte: 0x%X != 0x%X" % (som, DMXUSBCodes['SOM']))
		
		label = struct.unpack('B', str(in_str)[1])[0]
		if label not in sorted(DMXUSBLabels.keys())[:-3]:
			raise DMXUSBError("String has invalid label: %d" % label)
			
		size = struct.unpack('<H', str(in_str)[2:4])[0]
		if size > self.packetMaxData:
			raise DMXUSBError("String has invalid size: %d > %d" % (size, self.packetMaxData))
		if size != (len(in_str) - 5):
			raise DMXUSBError("String has invalid size: %d != %d" % (size, len(in_str) - 5))
		
		eom = struct.unpack('B', str(in_str)[-1])[0]
		if eom != DMXUSBCodes['EOM']:
			raise DMXUSBError("String has invalid EOM byte: 0x%X != 0x%X" % (eom, DMXUSBCodes['EOM']))
		
		self.data = list(str(in_str))[:self.packetMaxData + 5]
	
	def copy(self):
		"""Return a new DMXUSBPacket instance of the same type and with the same slot-values.
		"""
		new = self.__class__()
		new.data = self.data[:]
		return new
	
	def setLabel(self, label):
		"""Change the label (i.e. type) of the DMXUSBPacket
		Valid labels for outgoing packets are:
		 1	'PROG_FIRMW_REQ'	Program Firmware Request
		 2	'PROG_FLASH_PAGE'	Program Flash Page
		 3	'GET_WIDGET_PARAMS'	Widget Parameters Request
		 4	'SET_WIDGET_PARAMS'	Set Widget Parameters
		 6	'TX_DMX_ONLY	Transmit DMX packet (forever)
		 7	'TX_DMX_RX_DMX'	Transmit DMX packet, then Receive DMX packet (label 5)
		 8	'DMX_RX_ON_CHG_REQ'	Set 'DMX Receive on Change' mode
		10	'GET_WIDGET_SERIAL'	Widget Serial-number Request
		11	'TX_RDM_DISC'	RDM Discovery Request
		"""
		if label == None:
			label = 0
		elif label in DMXUSBCodes:
			label = DMXUSBCodes[label]
		elif label not in DMXUSBLabels:
			raise DMXUSBError("Invalid label: '%s'" % str(label))
		
		self.data[1] = struct.pack('B', label)
		
	setType = setLabel
		
	def getLabel(self):
		"""Return the DMXUSBPacket label as an integer
		Valid labels of incoming packets are:
		 2	Program Flash Page Reply
		 3	Widget Parameters Reply
		 5	Received DMX packet
		 9	Recieved 'DMX Change of State' packet
		10	Widget Serial-number Reply
		"""
		return struct.unpack('B', self.data[1])[0]
	
	def getType(self):
		"""Return the DMXUSBPacket label as a string
		Valid labels of incoming packets are:
		'PROG_FLASH_PAGE'	Program Flash Page Reply
		'GET_WIDGET_PARAMS'	Widget Parameters Reply
		'RX_DMX'		Received DMX packet
		'RX_DMX_CHG'	Recieved 'DMX Change of State' packet
		'GET_WIDGET_SERIAL'	Widget Serial-number Reply
		"""
		return DMXUSBLabels[self.getLabel()]
	
	def setData(self, data):
		"""Change the data-block of this DMXUSBPacket
		The provided argument can be a string or a list of ints
		"""
		if isinstance(data, DMXPacket):
			size = len(data) + 1
			self.data[4:-1] = list(str(data))
		if type(data) in types.StringTypes:
			data = data[:self.packetMaxData]
			size = len(data)
			self.data[4:-1] = list(str(data))
		elif type(data) == types.ListType:
			data = data[:self.packetMaxData]
			size = len(data)
			self.data[4:-1] = list(struct.pack('B' * size, *data))
		elif type(data) == types.IntType:
			size = 1
			self.data[4:-1] = list(struct.pack('B', data))
		else:
			raise TypeError("Provided argument must be a DMXPacket, a string, an int or a list of ints")
			
		self.data[2:4] = list(struct.pack('<H', size))

	def getDataBlock(self):
		"""Return the DMXUSBPacket's data-block as a sting
		"""
		return string.join(self.data[4:-1], '')
		
	def getDataValues(self):
		"""Return the DMXUSBPacket's data-block as a list of ints
		"""
		fmt = 'B' * len(self)
		return list(struct.unpack(fmt, self.getDataBlock()))
	
	def clearData(self):
		"""Remove the data-block from this DMXUSBPacket
		"""
		del self.data[4:-1]
		
	def clear(self, label=None):
		"""Remove the data-block from this DMXUSBPacket,
		and change the DMXUSBPacket's label (i.e. type) to the given type. If no label is provided, it defaults to '0',
		which is NOT a valid 'USB DMX Pro' message-type. A valid label must be set before the packet is sent.
		(see DMXUSBPacket.setLabel(...) for a list of valid label values)
		"""
		self.clearData()
		self.setLabel(label)
		
	def setDataFields(self, fields):
		"""Set or change the data-block contents on a field-by-field basis.
		Provided arg should be a dict with '<field-name>':value pairs.
		The field-names, field-sizes & field-types are defined in the TX_Fields list
		"""
		data_str = self.getDataBlock()
		idx = 0
		field_count = 0
		for (name, size, format) in self.TX_Fields:
			end = idx + size
			field_count += 1
			
			if name in fields:
				data = fields[name]
				if ((isinstance(data, DMXPacket)) and (format == 'D') or (type(data) in types.StringTypes)):
					field_str = str(data)
				elif type(data) == types.ListType:
					fmt = '<' + (format * len(data))
					field_str = struct.pack(fmt, *data)
				elif type(data) == types.IntType:
					fmt = '<' + format
					field_str = struct.pack(fmt, data)
				else:
					raise TypeError("%s field value must be a string or (list of) int" % name)
				
				if field_count < len(self.TX_Fields):			# if not last field
					field_str = field_str.ljust(size, '\x00')	# zero-pad if field_str is shorter
				
				field_str = field_str[:size]				# truncate if field_str is longer
			
				head = data_str[:idx]
				tail = data_str[end:]
				data_str = head + field_str + tail
			
			elif field_count < len(self.TX_Fields):			# if not last field
				field_str = data_str[idx:end]
				if len(field_str) < size:						# field too short
					data_str = data_str.ljust(end, '\x00')
				
			#print "Field '%s' [%d:%d] = %s" % (name, idx, end, repr(field_str))
			#print "Data = %s" % repr(data_str)
				
			idx = end
		
		self.setData(data_str)
		
	def getDataFields(self):
		"""Return a dict with '<field-name>':<value> pairs
		"""
		data_str = self.getDataBlock()
		out = {}
		for (name, size, format) in self.RX_Fields:
			if not len(data_str):
				break
			
			field_str = data_str[:size]
			data_str = data_str[size:]
			field = None
			if format == 'B':			# bytes
				field = list(struct.unpack('B' * len(field_str), field_str))
			elif format == 'H':		# a 16-bit Little-Endian short int
				field = struct.unpack('<H', field_str)[0]
			elif format == 'L':		# a 40-bit Little-Endian long int
				tmp = struct.unpack('<BL', field_str)
				field = tmp[0] | (256 * tmp[1])
			elif format == 'c':		# characters (i.e. a string)
				field = field_str
			elif format == 'x':		# a 32-bit Little-Endian long int, cast to a hex string
				tmp = struct.unpack('<L', field_str)[0]
				field = '0x%X' % tmp
			elif format == 'D':		# a DMX packet
				field = DMXReceive(field_str)
					
			if (type(field) == types.ListType) and (len(field) == 1):
				out[name] = field[0]
			else:
				out[name] = field
				
		return out
		
	def getDataField(self, name):
		"""Return the decoded value of the given field.
		Valid field-names, as well as the field's size & type, are defined in RX_Fields
		"""
		fields = self.getDataFields()
		if name in fields:
			return fields[name]
		
		return None
		
		
###
# Specific DMXUSB Packets 
###

class DMXUSBProgFirmwPacket(DMXUSBPacket):
	"""Class for the 'Program Firmware' Request, with label == 1
	"""
	
	packetMaxData = 0
	
	TX_Fields = []
	RX_Fields = TX_Fields
	
	def __init__(self):
		"""Set-up the DMXUSBProgFirmwPacket
		"""
		super(self.__class__, self).__init__(1)
		
		
class DMXUSBProgFlashPacket(DMXUSBPacket):
	"""Class for the 'Program Flash Page' Request / Reply, with label == 2
	"""
	
	packetMaxData = 64
	
	TX_Fields = [('data', packetMaxData, 'B')]
	RX_Fields = [('ack', 4, 'c')]
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBProgFlashPacket.
		The Flash-Page data can be provided in the 'data' argument.
		'data' can be a string or a list of 8-bit integers (of length 64, in either case)
		or 'data' can be a dict with '<field-name>':<value> pairs.
		Valid fields are (defined in TX_Fields)
		'data':	a string or list of ints (of length 64)
		"""
		super(self.__class__, self).__init__(2)
		
		if type(data) == types.DictType:
			self.setDataFields(data)
		elif data != None:
			self.setData(data)


class DMXUSBGetWidgetParamsPacket(DMXUSBPacket):
	"""Class for the 'Get Widget PArameters' Request  / Reply, with label == 3
	"""
	
	packetMaxData = 513
	
	TX_Fields = [('user_size', 2, 'H')]
	RX_Fields = [('version', 2, 'B'), ('dmx_brk_time', 1, 'B'), ('dmx_mab_time', 1, 'B'), ('dmx_rate', 1, 'B'), ('user', 508, 'B')]
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBGetWidgetParamsPacket. 
		The size of the user-data block to be returned can be specified with the 'data' argument
		'data' can be a string (of length 2) or a 16-bit integer
		or 'data' can be a dict with '<field-name>':<value> pairs.
		Valid fields are (defined in TX_Fields):
		'user_size'	(0 - 508):	User-config block size
		"""
		super(self.__class__, self).__init__(3)
		
		if type(data) == types.DictType:
			self.setDataFields(data)
		elif data != None:
			self.setData(data)		
		

class DMXUSBSetWidgetParamsPacket(DMXUSBPacket):
	"""Class for the 'Set Widget PArameters' Request, with label == 4
	"""
	
	packetMaxData = 513
	
	TX_Fields = [('user_size', 2, 'H'), ('dmx_brk_time', 1, 'B'), ('dmx_mab_time', 1, 'B'), ('dmx_rate', 1, 'B'), ('user', 508, 'B')]
	RX_Fields = TX_Fields
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBSetWidgetParamsPacket.
		The fields in the data-block can be set using the 'data' argument
		'data' can be a string (of length 5 - 513) or a list of integers (of length 4 - 512) where
		the first int (the 'user_size' value) is a 16-bit int, with value (len('data') - 4) all other ints are 8-bit values.
		Preferably though, 'data' should be a dict with '<field-name>':<value> pairs.
		Valid fields are (defined in TX_Fields):
		'user_size'		(0 - 508)	User-config block size
		'dmx_brk_time'	(9 - 127)	DMX 'Break' time
		'dmx_mab_time'	(1 - 127)	DMX 'Mark after Break' time
		'dmx_rate'		(0 - 40)	DMX TX rate
		'user'			upto 508 bytes; User-config block.
		The 'user' field may be a string or a list of (8-bit) integers
		The 'user_size' field will be set to the correct value automatically if the 'user' field is specified
		"""
		super(self.__class__, self).__init__(4)
		
		if type(data) == types.DictType:
			self.setDataFields(data)
		elif data != None:
			self.setData(data)		
			
	def setDataFields(self, fields):
		"""Set or change the data-block contents on a field-by-field basis.
		Provided arg should be a dict with '<field-name>':value pairs.
		The field-names, field-sizes & field-types are defined in the TX_Fields list
		The 'user_size' field will be set to the correct value automatically if the 'user' field is specified
		"""
		if 'user' in fields:
			fields['user'] = fields['user'][:self.TX_Fields[4][1]]
			fields['user_size'] = len(fields['user'])
		
		super(self.__class__, self).setDataFields(fields)

class DMXUSBReceivedPacket(DMXUSBPacket):
	"""Class for the 'Received DMX' Reply, with label == 5
	"""
	
	packetMaxData = 514
	
	TX_Fields = []
	RX_Fields = [('err', 1, 'B'), ('dmx', 513, 'D')]
	
	def __init__(self):
		"""Set-up the DMXUSBReceivedPacket.
		"""
		super(self.__class__, self).__init__(5)
	

class DMXUSBSendForeverPacket(DMXUSBPacket):
	"""Class for the 'Send DMX, TX Only' Request, with label == 6
	"""
	
	packetMaxData = 513
	
	TX_Fields = [('dmx', 513, 'D')]
	RX_Fields = TX_Fields
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBSendForeverPacket. The encapsulated DMX data may be given in the 'data' argument
		'data' can be a DMXPacket-object, a string or a list of (8-bit) integers
		or 'data' can be a dict with '<field-name>':<value> pairs.
		Valid fields are (defined in TX_Fields):
		'dmx':	the DMX data (DMXPacket, string or list of ints)
		"""
		super(self.__class__, self).__init__(6)
	
		if isinstance(data, DMXPacket):
			self.setData(str(data))
		elif type(data) == types.DictType:
			self.setDataFields(data)
		elif data != None:
			self.setData(data)


class DMXUSBSendOncePacket(DMXUSBPacket):
	"""Class for the 'Send DMX, then Receive DMX' Request, with label == 7
	"""
	
	packetMaxData = 513
	
	TX_Fields = [('dmx', 513, 'D')]
	RX_Fields = TX_Fields
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBSendOncePacket. The encapsulated DMX data may be given in the 'data' argument
		'data' can be a DMXPacket-object, a string or a list of (8-bit) integers
		or 'data' can be a dict with '<field-name>':<value> pairs.
		Valid fields are (defined in TX_Fields):
		'dmx':	the DMX data (DMXPacket, string or list of ints)
		"""
		super(self.__class__, self).__init__(7)
	
		if isinstance(data, DMXPacket):
			self.setData(str(data))
		elif type(data) == types.DictType:
			self.setDataFields(data)
		elif data != None:
			self.setData(data)


class DMXUSBSetRxOnChgPacket(DMXUSBPacket):
	"""Class for the 'Set Receive DMX On Change Mode' Request, with label == 8
	"""
	
	packetMaxData = 1
	
	TX_Fields = [('mode', 1, 'B')]
	RX_Fields = TX_Fields
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBSetRxOnChgPacket. The 'DMX USB Pro' box' operating mode can be set wit hthe 'data' argument
		'data' can be a string or list of ints (of length 1, in either case) or a single integer
		or 'data' can be a dict with '<field-name>':<value> pairs.
		Valid fields are (defined in TX_Fields):
		'mode'	(0 or 1)	Operating mode: 
			mode 0 = 'Receive Always'; device sends DMXUSBReceivedPackets continuously
			mode 1 = 'Receive Data On Change'; device sends DMXUSBReceivedChangedStatePackets when DMX-slot values change
		"""
		super(self.__class__, self).__init__(8)
		
		if type(data) == types.DictType:
			self.setDataFields(data)
		elif data != None:
			self.setData(data)		

class DMXUSBReceivedChangedStatePacket(DMXUSBPacket):
	"""Class for the 'DMX Changed State' Reply, with label == 9
	"""
	
	packetMaxData = 46
	
	TX_Fields = []
	RX_Fields = [('start', 1, 'B'), ('mask', 5, 'L'), ('slots', 40, 'B')]
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBReceivedChangedStatePacket
		The provided 'data' argument, if any, should be the DMXPacket reflecting the 'current state', 
		to which the received changes are applied.
		'data' can be a DMXPacket instance, a list of DMX-slot values or 'raw' DMX-packet data (i.e. a string).
		The latter two will be converted to a DMXPacket object first.
		If no DMX data is set before getDataField() or getDataFields() is called, an empty DMXPacket will be created.
		The getDataFields() method will return the changed DMXPacket in the 'dmx' field.
		"""
		super(self.__class__, self).__init__(9)
		
		if isinstance(data, DMXPacket):
			self.dmx = data
		elif type(data) == types.ListType:
			self.dmx = DMXPacket()
			self.dmx[1:] = data
		elif data in types.StringTypes:
			self.dmx = DMXPacket()
			self.dmx.fromString(data)
		elif data == None:
			self.dmx = DMXPacket()
		else:
			raise TypeError("Provided argument must be a DMXPacket, a string or a list of ints")

	def setData(self, data):
		"""Change the 'current state' DMX data held by this DMXUSBReceivedChangedStatePacket
		The provided argument can be a DMXPacket instance, a string or a list of ints
		"""
		if isinstance(data, DMXPacket):
			self.dmx = data
		elif type(data) == types.ListType:
			self.dmx = DMXPacket()
			self.dmx[1:] = data
		elif type(data) in types.StringTypes:
			self.dmx = DMXPacket()
			self.dmx.fromString(data)
		else:
			raise TypeError("Provided argument must be a DMXPacket, a string or a list of ints")

	def getDataFields(self):
		"""Return a dict with '<field-name>':<value> pairs
		This method parses the 'start', 'mask' and 'slots' fields of the received packet
		and applies the slot-changes to the 'current state' DMXPacket held by this DMXUSBReceivedChangedStatePacket
		The updated DMXPacket is returned in the 'dmx' field
		"""
		fields = super(self.__class__, self).getDataFields()
		
		idx = 0
		for bit in range(40):
			if (fields['mask'] & (2 ** bit)) != 0:
				slot = (fields['start'] * 8) + bit
				self.dmx[slot] = fields['slots'][idx]
				idx += 1
				
		return {'dmx':self.dmx}

class DMXUSBGetWidgetSerialPacket(DMXUSBPacket):
	"""Class for the 'Get Widget Serial-number' Request / Reply, with label == 10
	"""
	
	packetMaxData = 4
	
	TX_Fields = []
	RX_Fields = [('serial', 4, 'x')]
	
	def __init__(self):
		"""Set-up the DMXUSBGetWidgetSerialPacket
		"""
		super(self.__class__, self).__init__(10)
		

class DMXUSBSendRDMDiscoveryPacket(DMXUSBPacket):
	"""Class for the 'Send RDM Discovery' Request, with label == 11
	"""
	
	packetMaxData = 38
	
	TX_Fields = [('rdm', 38, 'B')]
	RX_Fields = TX_Fields
	
	def __init__(self, data=None):
		"""Set-up the DMXUSBReceivedPacket. 
		The RDM Request data can be provided in the 'data' argument.
		'data' can be a string or a list of 8-bit integers (of length 38, in either case)
		or 'data' can be a dict with '<field-name>':<value> pairs.
		Valid fields are (defined in TX_Fields)
		'rdm':	a string or list of ints (of length 38)
		"""
		super(self.__class__, self).__init__(7)
	
		if type(data) == types.DictType:
			self.setDataFields(data)
		elif data != None:
			self.setData(data)


###
# DMX USB Pro box interface 
###

class DMXUSBPro(object):
	"""Class (object) to interface with the Enttec 'DMX USB Pro' box
	"""
	def __init__(self, serport='/dev/ttyUSB0'):
		"""Initialize & open the specified (USB-)serial port
		Confirm weather a 'DMX USB Pro' box is in fact connected by exchanging the
		'GET_WIDGET_PARAMS' and 'GET_WIDGET_SERIAL' messages
		"""
		self.ser = serial.Serial(serport)
		self.setTimeout(1)
		
		self.dmx_in = DMXPacket()
		self.dmx_out = None
		
		self.rx_mode = 0
		self.tx_mode = 1
		
		try:
			self.params = self.getWidgetParams()
			self.serial = self.getWidgetSerial()
			
		except:
			self.close()
			raise

	def __str__(self):
		out = "DMX USB Pro "
		if 'version' in self.params:
			out += "v%d.%d " % (self.params['version'][1], self.params['version'][0])
		out += "(#%s) " % self.serial
		out += "on %s" % self.ser.portstr
	
		return out
	
	def close(self):
		"""Close the device's (USB-)serial port
		"""
		self.ser.close()
	
	def setTimeout(self, timeout):
		"""Set serial-port timeout
		"""
		self.ser.setTimeout(timeout)
	
	def send(self, packet):
		"""Send a DMXUSBPacket to the box
		The provided argument can be a DMXUSB*Packet instance or a string,
		in which case the string is first turned into a USBDMXPacket
		"""
		if isinstance(packet, DMXUSBPacket):
			out = str(packet)
		elif type(packet) in types.StringTypes:
			p = DMXUSBPacket()		# cast string to USBDMXPacket
			p.fromString(packet)	# some checks are done on the provided string
			out = str(p)			# and cast back to string
		else:
			raise TypeError("Provided argument must be a DMXUSBPacket, or a string representaion of a valid DMXUSBPacket")

		self.ser.write(out)
		self.ser.flush()		# wait for all data to be sent
		
	def receive(self):
		"""Recieve a USBDMX*Packet from the box.
		The label (i.e. type) of the received string is checked, and the appropriate USBDMX*Packet-type is returned.
		May return 'None' if the serial read times-out or returns an empty string.
		"""
		try:
			in_str = self.ser.readline(eol='%c' % DMXUSBCodes['EOM'])
		except serial.SerialTimeoutException:
			return None
		
		if not len(in_str):
			return None
		
		if len(in_str) < 5:
			raise DMXUSBError("Received data too short for DMXUSBPacket. (%d bytes)" % len(in_str))
		
		label = struct.unpack('B', str(in_str)[1])[0]
		
		if label == DMXUSBCodes['PROG_FIRMW_REQ']:
			packet = DMXUSBProgFirmwPacket()
		elif label == DMXUSBCodes['PROG_FLASH_PAGE']:
			packet = DMXUSBProgFlashPacket()
		elif label == DMXUSBCodes['GET_WIDGET_PARAMS']:
			packet = DMXUSBGetWidgetParamsPacket()
		elif label == DMXUSBCodes['SET_WIDGET_PARAMS']:
			packet = DMXUSBSetWidgetParamsPacket()
		elif label == DMXUSBCodes['RX_DMX']:
			packet = DMXUSBReceivedPacket()
		elif label == DMXUSBCodes['TX_DMX_ONLY']:
			packet = DMXUSBSendForeverPacket()
		elif label == DMXUSBCodes['TX_DMX_RX_DMX']:
			packet = DMXUSBSendOncePacket()
		elif label == DMXUSBCodes['DMX_RX_ON_CHG_REQ']:
			packet = DMXUSBSetRxOnChgPacket()
		elif label == DMXUSBCodes['RX_DMX_CHG']:
			packet = DMXUSBReceivedChangedStatePacket(self.dmx_in)
		elif label == DMXUSBCodes['GET_WIDGET_SERIAL']:
			packet = DMXUSBGetWidgetSerialPacket()
		elif label == DMXUSBCodes['TX_RDM_DISC']:
			packet = DMXUSBSendRDMDiscoveryPacket()
		else:
			packet = DMXUSBPacket()
			
		packet.fromString(in_str)
		
		return packet

	def getWidgetParams(self, user_size=0):
		"""Send a 'GET_WIDGET_PARAMS' request to the box
		Receive and parse a 'GET_WIDGET_PARAMS' reply from the box.
		The parameters are stored in DMXUSBPro.params (as a dict)
		"""
		p_out = DMXUSBGetWidgetParamsPacket()
		p_out.setDataFields({'user_size':user_size})
		
		self.send(p_out)
		
		p_in = self.receive()
		
		if p_in == None:
			raise DMXUSBError("Packet Receive timed out")
		
		if not isinstance(p_in, DMXUSBGetWidgetParamsPacket):
			raise DMXUSBError("Expected 'GET_WIDGET_PARAMS' reply, got '%s'" % p_in.getType())
		
		return p_in.getDataFields()

	def setWidgetParams(self, dmx_rate=None, dmx_brk_time=None, dmx_mab_time=None, user=None):
		"""Change any pf the box' parameters to the values provided
		The parameters are stored in DMXUSBPro.params (as a dict)
		Send a 'SET_WIDGET_PARAMS' request to the box
		"""
		if (type(dmx_rate) == types.IntType) and (dmx_rate >= 0) and (dmx_rate <= 40):
			self.params['dmx_rate'] = dmx_rate
		
		if (type(dmx_brk_time) == types.IntType) and (dmx_brk_time >= 9) and (dmx_brk_time <= 127):
			self.params['dmx_brk_time'] = dmx_brk_time
		
		if (type(dmx_mab_time) == types.IntType) and (dmx_mab_time >= 1) and (dmx_mab_time <= 127):
			self.params['dmx_mab_time'] = dmx_mab_time
		
		if user != None:
			self.params['user'] = user
			
		p_out = DMXUSBSetWidgetParamsPacket()
		p_out.setDataFields(self.params)
		
		self.send(p_out)
	
	def getWidgetSerial(self):
		"""Send a 'GET_WIDGET_SERIAL' request to the box
		Receive and parse a 'GET_WIDGET_SERIAL' reply from the box.
		The serial-number are stored in DMXUSBPro.serial (as a string of hexadecimal numbers)
		"""
		p_out = DMXUSBGetWidgetSerialPacket()
		
		self.send(p_out)
		
		p_in = self.receive()
		
		if p_in == None:
			raise DMXUSBError("Packet Receive timed out")
		
		if not isinstance(p_in, DMXUSBGetWidgetSerialPacket):
			raise DMXUSBError("Expected 'GET_WIDGET_SERIAL' reply, got '%s'" % p_in.getType())
		
		return p_in.getDataField('serial')
		
	def getDMXPacket(self):
		"""Receive a 'RX_DMX' message from the box
		Returned dict has 2 items:
		'err':	Receiver error-code (0 - 3)
		'dmx':	DMXPacket-object
		"""
		p_in = self.receive()
		
		if p_in == None:
			raise DMXUSBError("Packet Receive timed out")
		
		if not isinstance(p_in, DMXUSBReceivedPacket):
			raise DMXUSBError("Expected 'RX_DMX' reply, got '%s'" % p_in.getType())
		
		fields = p_in.getDataFields()
		
		if ('err' in fields) and fields['err'] == 0:
			if ('dmx' in fields) and isinstance(fields['dmx'], DMXPacket):
				self.dmx_in = fields['dmx']
		
		return fields
	
	def sendDMXPacketForever(self, dmx_packet):
		"""Send a 'TX_DMX_ONLY' request to the box.
		The box will continuously re-transmit the DMXPacket.
		"""
		p_out = DMXUSBSendForeverPacket()
		p_out.setDataFields({'dmx':dmx_packet})
		
		self.send(p_out)
		self.dmx_out = p_out.getDataField('dmx')
		
	def sendDMXPacketOnce(self, dmx_packet):
		"""Send a 'TX_DMX_RX_DMX' request to the box.
		The box will transmit the DMXPacket once, then switch to receive mode.
		The getDMXPacket() or getDMXOnChangePacket() method should be called next,
		or the receiveDMX() method, which automatically selects between these two
		"""
		p_out = DMXUSBSendOncePacket()
		p_out.setDataFields({'dmx':dmx_packet})
		
		self.send(p_out)
		self.dmx_out = p_out.getDataField('dmx')
		
	def sendRDMDiscovery(self, rdm_packet):
		"""Send a 'TX_RDM_DISC' request to the box
		"""
		p_out = DMXUSBSendRDMDiscoveryPacket()
		p_out.setDataFields({'rdm':rdm_packet})
		
		self.send(p_out)
		
	def setDMXRXOnChange(self, mode=True):
		"""Send a 'DMX_RX_ON_CHG_REQ' request to the box
		If 'mode' is True (or nonzero), the 'Receive DMX On Change' mode is selected
		If 'mode' is False (or zero), the 'Receive DMX Always' mode is selected
		"""
		if mode:
			mode = 1
		else:
			mode = 0
		
		p_out = DMXUSBSetRxOnChgPacket()
		p_out.setDataFields({'mode':mode})
		
		self.send(p_out)
		self.rx_mode = p_out.getDataField('mode')
		
	def getDMXRXOnChange(self):
		"""Returns the DMX reception mode currently set
		'0' means using 'RX_DMX'
		'1' means using 'RX_DMX_CHG'
		"""
		return self.rx_mode
	
	def getDMXOnChangePacket(self):
		"""Receive a 'RX_DMX_CHG' message from the box
		The changed DMX-slots carried in the message are applied to the 'current state' DMXPacket 
		(in DMXUSBPro.dmx_in). This updated DMXPacket is also returned (in the dict) 
		Returned dict has 1 items:
		'dmx':	DMXPacket-object
		"""
		p_in = self.receive()
		
		if p_in == None:
			raise DMXUSBError("Packet Receive timed out")
		
		if not isinstance(p_in, DMXUSBReceivedChangedStatePacket):
			raise DMXUSBError("Expected 'RX_DMX_CHG' reply, got '%s'" % p_in.getType())
		
		return p_in.getDataFields()
		
	def receiveDMX(self):
		"""Receive a DMXPacket, using the currently set DMX reception mode
		If rx_mode is 0, the 'RX_DMX' message is used
		If rx_mode is 1, the 'RX_DMX_CHG' message is used
		(see setDMXRXOnChange(...) and getDMXRXOnChange())
		
		Raises a DMXUSBError when the DMXUSBPro box signals a reception-error
		"""
		if self.rx_mode == 0:
			fields = self.getDMXPacket()
		else:
			fields = self.getDMXOnChangePacket()
			
		if ('err' in fields) and (fields['err'] != 0):
			raise DMXUSBError("Error receiving DMX: %d" % fields['err'])
		
		return fields['dmx']
		
	def setDMXTXForever(self, mode=True):
		"""Sets the TX mode for the sendDMX(...) method
		If 'mode' is True (or nonzero), the 'TX_DMX_ONLY' message is used
		If 'mode' is False (or zero), the 'TX_DMX_RX_DMX' message is used
		"""
		if mode:
			self.tx_mode = 1
		else:
			self.tx_mode = 0
		
	def getDMXTXForever(self):
		"""Returns the DMX transmission mode currently set.
		'1' means using 'TX_DMX_ONLY'
		'0' means using 'TX_DMX_RX_DMX'
		"""
		return self.tx_mode
	
	def sendDMX(self, dmx_packet, mode=None):
		"""Send a DMXPacket to the box, in one of two ways;
		If 'mode' is True (or nonzero), the 'TX_DMX_ONLY' message is used
		The DMXPacket is re-transmitted continuously.
		If 'mode' is False (or zero), the 'TX_DMX_RX_DMX' message is used
		The DMXPacket is transmitted once, then the box switches to receive mode.
		The getDMXPacket() or getDMXOnChangePacket() method should be called next,
		or the receiveDMX() method, which automatically selects between these two.
		
		If 'mode' is None (the default), the DMX transmission mode is unchanged.
		(see setDMXTXForever(...) and getDMXTXForever())
		"""
		if mode != None:
			self.setDMXTXForever(mode)
			
		if self.tx_mode:
			self.sendDMXPacketForever(dmx_packet)
		else:
			self.sendDMXPacketOnce(dmx_packet)
	
	def progFirmware(self, fw_file):
		ff = open(fw_file, 'rb')
		
		p_out = DMXUSBProgFirmwPacket()
		
		self.send(p)
		
		time.sleep(0.2)
		
		p_out = DMXUSBProgFlashPacket()
		
		data = ff.read(p_out.packetMaxData)
		pg_cnt = 0
		while len(data):
			p_out.setDataFields({'data':data})
			
			self.send(p_out)
			
			p_in = self.receive()
			
			if not isinstance(p_in, DMXUSBProgFlashPacket):
				ff.close()
				raise DMXUSBError("Expected 'PROG_FLASH_PAGE' reply, got '%s'" % p_in.getType())

			ack = p_in.getDataField('ack')
			
			if ack != 'TRUE':
				ff.close()
				raise DMXUSBError("Error programming Flash-page %d" % pg_cnt)
				
			pg_cnt += 1
			data = ff.read(p_out.packetMaxData)

