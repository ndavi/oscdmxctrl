#!/usr/bin/python

###
# DMX512 Protocol Classes
###
# A Set of classes to encapsulate DMX512 messages as Python Objects
# These objects emulate container-types (i.e. lists) to some extent.
#
# A convenience function 'DMXReceive(...)' is also provided. This function
# parses a given input-string into the appropriate DMX*Packet object, and returns this object
#
# Stock, V2_Lab Rotterdam, Aug 2008
###

###
# Changelog
###
# version 0.1
#	initial version
###

import types, string, struct


global DMX512PacketTypes
DMX512PacketTypes = { 0x00:'NULL', 0x17:'TEXT', 0x55:'TEST', 0x91:'MFID', 0xCF:'SIP', 
						0xF0:'TMP0', 0xF1:'TMP1', 0xF2:'TMP2', 0xF3:'TMP3', 0xF4:'TMP4', 0xF5:'TMP5', 0xF6:'TMP6', 0xF7:'TMP7', }

global DMX512PacketNumbers
DMX512PacketNumbers = dict(zip(DMX512PacketTypes.values(), DMX512PacketTypes.keys()))


class DMXError(BaseException):
	pass


class DMXPacket(object):
	"""Class to build or decode DMX512 packets
	"""
	packetMaxSlots = 512
	
	def __init__(self, startcode=None):
		"""Set-up a new DMXPacket.
		The DMXPacket's startcode may be provided, but if it isn't, the default ('NULL') startcode '0' is used.
		Other valid startcodes are:
		0x17 (23)	TEXT packet, to send ascii strings over DMX
		0x55 (85)	TEST packet, a packet with all 512 slots set to '85', normally
		0x91 (145)	MFID packet, the first two slots contain a 16-bit Manufacturer-ID,
				the remaining slots may contain proprietary data
		0xCF (207)	SI packet, system-information packet, normally with 24 slots containing various data
				in pre-defined fields (see DMXSIPacket)
		"""
		if startcode == None:
			startcode = 0
		elif startcode in DMX512PacketNumbers:
			startcode = DMX512PacketNumbers[startcode]
		elif startcode not in DMX512PacketTypes:
			raise DMXError("Invalid startcode: '%s'" % str(startcode))
		
		self.slots = [struct.pack('B', startcode)]
		
	def __str__(self):
		"""Return the DMXPacket as a string
		"""
		return string.join(self.slots, '')
	
	def __len__(self):
		"""Return the number of slots in the DMXPacket
		"""
		return (len(self.slots) - 1)
	
	def __repr__(self):
		"""Return the DMXPacket as a human-readable string
		"""
		bytes = str(self)
		startcode = struct.unpack('B', bytes[0])[0]
		out = "<DMXPacket %s: " % DMX512PacketTypes[startcode]
		if len(self):
			fmt = 'B' * len(self)
			out += str(struct.unpack(fmt, bytes[1:]))
		out += ">"
		return out
		
	def __getitem__(self, which):
		"""Return the decoded contents of the given slot.
		With a 'slice' argument, return the decoded contents of the given slots as a list.
		"""
		if type(which) == types.IntType:
			item = self.slots[which]
			return struct.unpack('B', item)[0]
		elif type(which) == types.SliceType:
			items = string.join(self.slots[which], '')
			fmt = 'B' * len(items)
			return list(struct.unpack(fmt, items))
	
	def __setitem__(self, which, value):
		"""Encode and set the given value in the given slot.
		With a 'slice' argument, sets the given slots to the given values (the 'value' arg must be a list or tuple, in that case)
		If necessary, the number of slots (i.e. the Universe) will be expanded and/or truncated at packetMaxSlots
		"""
		if type(value) in types.StringTypes:
			value = list(str(value))
		if type(value) in (types.ListType, types.TupleType):
			num = len(value)
			if num == 1:
				value = value[0]
		else:
			num = 1
			
		if type(which) == types.IntType:
			if which > self.packetMaxSlots:
				raise IndexError("DMXPacket can only have %d slots" % self.packetMaxSlots)
			
			if num > 1:
				raise TypeError("Cannot set a single slot to multiple values '%s'" % str(value))
			
			if which >= len(self.slots):
				append = which - len(self.slots) + 1
				self.slots += ['\x00'] * append
		
		elif type(which) == types.SliceType:
			idx = which.indices(len(self.slots))
			if ((min(idx[0], idx[1]) + num - 1) > self.packetMaxSlots):
				raise IndexError("DMXPacket can only have %d slots" % self.packetMaxSlots)
				
		if num == 1:
			self.slots[which] = struct.pack('B', value)[0]
		else:
			fmt = 'B' * num
			self.slots[which] = list(struct.pack(fmt, *value))
			# nr of slots might have changed! truncate at maxlen
			self.slots = self.slots[:self.packetMaxSlots + 1]
		
	def __delitem__(self, which):
		"""Remove the given slot (or slots). All higher-numbered slots are shifted left
		(i.e. the DMXPacket length shrinks)
		"""
		del self.slots[which]
		
	def __iter__(self):
		"""Return an iterator over the DMXPacket's slots' decoded values
		"""
		bytes = str(self)[1:]
		fmt = 'B' * len(bytes)
		return struct.unpack(fmt, bytes).__iter__()
	
	def __contains__(self, value):
		"""Return 'True' if one of the slots' values is equal to the given value
		Return 'False' if the given value does not occur in any of the Packet's slots
		"""
		if type(value) == types.IntType:
			value = struct.pack('B', value)[0]
		elif type(value) in types.StringTypes:
			item = str(value)[0]
		else:
			raise TypeError("Can only search for int or char types in slot values")
			
		return (value in self.slots[1:])
	
	def __copy__(self):
		"""Return a new DMXPacket instance of the same type and with the same slot-values.
		"""
		new = self.__class__()
		new.slots = self.slots[:]
		return new
	
	copy = __copy__
	
	def __add__(self, other):
		"""Concatenate the slots of this DMXPacket with the slots of the other DMXPacket
		Returns a new DMXPacket of the same type as this DMXPacket and with the concatenated slots
		"""
		if not isinstance(other, self.__class__):
			raise TypeError("Concatenation is only supported between DMXPackets")
		
		new = DMXPacket()
		slots = self.slots + other.slots[1:]
		new.slots = slots[:self.packetMaxSlots]
		return new
	
	def append(self, value):
		"""Append a new slot, set to the given value
		"""
		if len(self.slots) > self.packetMaxSlots:
			raise IndexError("DMXPacket can only have %d slots" % self.packetMaxSlots)
		
		if type(value) == types.IntType:
			self.slots.append(struct.pack('B', value)[0])
		elif type(value) in types.StringTypes:
			self.slots.append(str(value)[0])
		else:
			raise TypeError("Slot value must be int or string: '%s'", str(value))
		
	def fromString(self, in_str):
		"""Parse the given string into the DMXPacket. The first char of the string sets the packet-type,
		the rest of the string's chars set slot-values
		"""
		if not ((type(in_str) in types.StringTypes) and len(in_str)):
			return
		
		startcode = struct.unpack('B', str(in_str)[0])[0]
		if startcode not in DMX512PacketTypes:
			raise DMXError("Invalid startcode: '%s'" % str(startcode))
			
		self.slots = list(str(in_str))[:self.packetMaxSlots + 1]
	
	def setStartcode(self, startcode):
		"""Change the packet's startcode (i.e. type)
		"""
		if startcode == None:
			startcode = 0
		elif startcode in DMX512PacketNumbers:
			startcode = DMX512PacketNumbers[startcode]
		elif startcode not in DMX512PacketTypes:
			raise DMXError("Invalid startcode: '%s'" % str(startcode))
		
		self.slots[0] = struct.pack('B', startcode)
		
	setType = setStartcode
	
	def getStartcode(self):
		"""Return the DMXPacket's startcode (i.e. type) as an integer
		"""
		return struct.unpack('B', self.slots[0])[0]
	
	def getType(self):
		"""Return the DMXPacket's type (i.e. startcode) as a string
		"""
		return DMX512PacketTypes[self.getStartcode()]
	
	def setSlot(self, which, value):
		"""Encode and set the given value in the given slot.
		If necessary, the number of slots (i.e. the Universe) will be expanded and/or truncated at packetMaxSlots
		"""
		if type(which) != types.IntType:
			raise TypeError("Slot index is not an integer: '%s'", str(which))
		
		if (which <= 0) or (which > self.packetMaxSlots):
			raise IndexError("Slot index must be in range (1, %d)" % self.packetMaxSlots)
		
		self.__setitem__(which, value)
		
	def getSlot(self, which):
		"""Return the decoded value of the given slot
		"""
		if type(which) != types.IntType:
			raise TypeError("Slot index is not an integer: '%s'", str(which))
		
		if (which <= 0) or (which > self.packetMaxSlots):
			raise IndexError("Slot index must be in range (1, %d)" % self.packetMaxSlots)
		
		return self.__getitem__(which)
	
	def getSlots(self):
		"""Return all slots' decoded values as a list
		"""
		return self[1:]
		
	def clearSlots(self):
		"""Remove all slots from the DMXPacket
		"""
		self.slots = self.slots[0:0]
		
	def clear(self, startcode=None):
		"""Remove all slots from the DMXPacket and set the Packet's startcode.
		Defaults to the 'NULL' packet (startcode '0') if no startcode is given.
		"""
		self.clearSlots()
		self.setStartcode(startcode)

	def chksum16(self):
		"""Calculate and return the DMXPacket's 16-bit additive checksum
		"""
		sum = 0
		fmt = 'B' * len(self.slots)
		for val in struct.unpack(fmt, str(self)):
			sum = (sum + val) % 0x10000
			
		return sum

class DMXTextPacket(DMXPacket):
	"""Special DMXPacket (with startcode = 0x17) for sending text messages
	Slot 1 contains a page-number, slot 2 sets the number of characters per line (where a value of '0' means no line-formatting happens)
	The remaining slots contain ascii-bytes
	"""
	def __init__(self, page=0, linelen=0, txt=None):
		"""Set-up a new DMXTextPacket with startcode 0x17.
		The page-number and line-length may be provided. 
		A line-length of 0 (the default) means no line-breaks are removed or inserted.
		The packet's text may also be provided
		"""
		super(self.__class__, self).__init__(startcode=0x17)
		self.setSlot(1, page)
		self.setSlot(2, linelen)
		
		self.packetMaxData = self.packetMaxSlots - 2
		
		if type(txt) in types.StringTypes:
			self.slots[3:] = list(str(txt))[:self.packetMaxData]
		
	def fromString(self, in_str):
		"""Parse the given string into the DMXTextPacket. The first char of the string sets the packet-type,
		the 2nd char sets the page-number,
		the 3rd char sets the line-length,
		and the rest of the string's chars are the text
		"""
		if (type(in_str) in types.StringTypes):
			if len(in_str) > 2:
				super(self.__class__, self).fromString(in_str)
			else:
				raise DMXError("Packet-string too short. Must set at least page-nr and line-length (3 chars in total)")
	
	def setText(self, txt):
		"""Set the DMXTextPacket's text
		The provided string is truncated at 510 characters
		"""
		if type(txt) not in types.StringTypes:
			raise TypeError("Not a string: '%s'" % str(txt))
		
		self.slots[3:] = list(str(txt))[:self.packetMaxData]
		
	def getText(self):
		"""Return the DMXTextPacket's text as a string.
		If the line-length (slot 2) != 0, existing line-breaks are removed, and new ones inserted.
		"""
		txt = string.join(self.slots[3:], '')
		linelen = self[2]
		if linelen == 0:
			return txt
		
		# remove any linebreaks provided
		txt = string.join(txt.splitlines())
		
		# insert line-breaks for the given line-length
		out = ""
		while len(txt):
			out += "%s\n" % txt[:linelen].strip()
			txt = txt[linelen:].strip()
			
		return out
	
	def setPage(self, num):
		"""Set the DMXTextPacket's page-number (in slot 1)
		"""
		self.setSlot(1, num)
		
	def getPage(self):
		"""Return the DMXTextPacket's page-number (from slot 1)
		"""
		return self[1]
	
	def setLineLen(self, num):
		"""Set the DMXTextPacket's line-length (in slot 2)
		"""
		self.setSlot(2, num)
		
	def getLinelen(self):
		"""Return the DMXTextPacket's line-length (from slot 2)
		"""
		return self[2]


class DMXTestPacket(DMXPacket):
	"""Special DMXPacket (with startcode = 0x55) for testing DMX512 networks
	All slots in this packet are set to 0x55
	"""
	def __init__(self):
		"""Set-up a new DMXTestPacket with startcode 0x55.
		All slots (see packetMaxSlots) in this packet are initially set to 0x55 
		(in binary form, 0x55 is '01010101')
		"""
		super(self.__class__, self).__init__(startcode=0x55)
		self[1:] = [0x55] * self.packetMaxSlots


class DMXMFIDPacket(DMXPacket):
	"""Special DMXPacket (with startcode = 0x91) for sending manufacturer- or device-specific proprietary data
	slot 1 & 2 contain a 16-bit Manufacturer-ID
	"""
	def __init__(self, mfid=0, data=None):
		"""Set-up a new DMXMFIDPacket with startcode 0x55.
		The Manufacturer-ID (a 16-bit value) may be provided. It is set to '0' if it isn't.
		Other propriatery data (upto 510 bytes) may also be provided as a string or a list/tuple of values
		"""
		super(self.__class__, self).__init__(startcode=0x91)
		self.slots[1:3] = list(struct.pack('>H', mfid))
		
		self.packetMaxData = self.packetMaxSlots - 2
		
		if type(data) in types.StringTypes:
			self.slots[3:] = list(data)[:self.packetMaxData]
		elif type(data) in (types.ListType, types.TupleType):
			fmt = 'B' * len(data)
			self.slots[3:] = list(struct.pack(fmt, *data))[:self.packetMaxData]
		
	def fromString(self, in_str):
		"""Parse the given string into the DMXMFIDPacket. The first char of the string sets the packet-type,
		the next 2 chars set the Manufacturer ID,
		and the rest of the string's chars are proprietary data
		"""
		if (type(in_str) in types.StringTypes):
			if len(in_str) > 2:
				super(self.__class__, self).fromString(in_str)
			else:
				raise DMXError("Packet-string too short. Must set at least startcode and mfid (3 chars in total)")
	
	def setData(self, data):
		"""Set the DMXMFIDPacket's proprietary data.
		The provided data (string, list or tuple) will be truncated at 510 items
		"""
		if type(data) in types.StringTypes:
			self.slots[3:] = list(data)[:self.packetMaxData]
		elif type(data) in (types.ListType, types.TupleType):
			fmt = 'B' * len(data)
			self.slots[3:] = list(struct.pack(fmt, *data))[:self.packetMaxData]
		else:
			raise TypeError("Not a string or list/tuple: '%s'" % str(data))
		
	def getDataStr(self):
		"""Return the DMXMFIDPacket's proprietary data as a string
		"""
		return string.join(self.slots[3:], '')
	
	def getData(self):
		"""Return the DMXMFIDPacket's proprietary data as a list
		"""
		data = self.getDataStr()
		fmt = 'B' * len(data)
		return list(struct.unpack(fmt, data))
	
	def setMFID(self, mfid):
		"""Set the DMXMFIDPacket's Manufacturer-ID (in slots 1 & 2)
		'mfid' should be an integer in range 0 - 65535
		"""
		if type(mfid) != types.IntType:
			raise TypeError("Not an integer ID-value: '%s'" % str(mfid))
		
		self.slots[1:3] = list(struct.pack('>H', mfid))
		
	def getMFID(self):
		"""Return the DMXMFIDPacket's Manufacturer-ID (from slots 1 & 2)
		"""
		mfid_str = string.join(self.slots[1:3], '')
		return struct.unpack('>H', mfid_str)[0]
	

class DMXSIPacket(DMXPacket):
	"""Special DMXPacket (with startcode = 0xCF) for System Information
	The SIPacket's slots become pre-defined fields:
	slot  1:	Slot count (a.k.a. SIP Checksum Pointer) [default is 24]
	slot  2:	Control Bit Field
	slot  3 &  4:	Checksum of Previous Packet
	slot  5:	Sequence Number
	slot  6:	DMX Universe Number
	slot  7:	DMX Processing Level
	slot  8:	Software Version
	slot  9 & 10:	Standard Packet Length (a.k.a. Universe Size)
	slot 11 & 12:	Nr of Packets sent since previous SIP
	slot 13 & 14:	Originating Device's MFID
	slot 15 & 16:	2nd Device's MFID
	...
	slot 21 & 22:	5th Device's MFID
	slot 23:	reserved
	...
	slot N:		Checksum of SIP (where 'N' is the value in slot 1)
		
	The SIP checksum is re-calculated whenever one or more fields are changed.
	"""
	packetMaxSlots = 255
	
	sipFields = { 	'size':(1, 'B'),
					'ctrl':(2, 'B'),
					'chksum':(3, '>H'),
					'seq':(5, 'B'),
					'uni':(6, 'B'),
					'level':(7, 'B'),
					'version':(8, 'B'),
					'length':(9, '>H'),
					'count':(11, '>H'),
					'mfids':((13, 15, 17, 19, 21), '>H')}
	
	def __init__(self, fields={}):
		"""Set-up a new DMXSIPacket with startcode 0xCF.
		The DMXSIPacket's fields can be set by providing a dict with '<field-name>':<value> pairs.
		see DMXSIPacket.setFields(...) for a list of possible field-names and value-ranges
		Omitted fields are initialized to '0', (except 'size', this field defaults to '24')
		"""
		super(self.__class__, self).__init__(startcode=0xCF)
		if 'size' not in fields:
			self.setSlot(1, 24)
			
		self.setFields(fields)
		
	def fromString(self, in_str, ignore_checksum=False):
		"""Parse the given string into the DMXSIPacket. The first char of the string sets the packet-type,
		the rest of the string's chars set the System Information fields
		This method checks if the string's length corresponds to the value specified in the 'size' field.
		Also tests the received 'SIP Checksum' value against the actual calculated checksum,
		unless the 'ignore_checksum' argument is 'True'
		"""
		if (type(in_str) in types.StringTypes):
			if len(in_str) <= 24:
				raise DMXError("Packet-string too short. Need at least 25 chars.")
			
			size = struct.unpack('B', str(in_str)[1])[0]
			if size < 24:
				raise DMXError("SIPacket-string has invalid 'size' value: %d < 24" % size)
			
			if len(in_str) == (size + 1):
				super(self.__class__, self).fromString(in_str)
			else:
				raise DMXError("Packet-string has incorrect length. Need %d chars, got %d" % (size + 1, len(in_str)))
			
			if not ignore_checksum: 
				if not self.testSIPChksum():
					raise DMXError("SIP Checksum error: %d != %d" % (self.getSIPChksum(), self.chksum8()))
	
	def _setField(self, slot, fmt, value):
		"""Set the field that strarts with the given slot to the given value (int or string), 
		using the given format ('B' for byte or '>H' for big-endian 16-bit value)
		"""
		if fmt == '>H':
			sz = 2
		else:
			sz = 1
		
		while len(self.slots) < slot:
			self.slots.append('\x00')
				
		if type(value) == types.IntType:
			self.slots[slot:slot + sz] = list(struct.pack(fmt, value))
		elif type(value) in types.StringTypes:
			self.slots[slot:slot + sz] = list(str(value)[:sz])
		
	def setFields(self, fields):
		"""Set one or more fields to a new value by providing a dict with '<field-name>':<value> pairs.
		Possible field-names and value-ranges are:
		
		'size' (24 - 255)	nr of slots in this DMXSIPacket (the default is 24)
		'ctrl' (0 - 3)		'Control Bit Field': 
					bit 0 sets 'subsequent NULL packet hold' to enable checksum-validation
					bit 1 sets 'previous packet was not a NULL packet'
		'chksum' (16 bits)	16-bit checksum of the preceding NULL packet
		'seq'	(0 - 255)	SIP sequence number.
		'uni'	(1 - 255)	DMX Universe number
		'level'	(0 - 255)	DMX Processing Level (i.e. DMX 'hop-counter')
		'version'(0 - 255)	Software version of last DMX-device
		'length'(0 - 512)	fixed NULL-packet size ('0' means 'not defined')
					bit 15 sets 'dynamic' packet size
		'count' (16 bits)	nr of packets transmitted since previous SIP
		'mfids' (list of 5 16-bit values)	Manufacturer-IDs of device-chain
		
		The SIP checksum is re-calculated and stored in the last slot whenever one or more fields are changed.
		"""
		if type(fields) != types.DictType:
			raise TypeError("Expected a dict with '<field-name>':<value> pairs")
		
		for (name, value) in fields.items():
			if name not in self.sipFields:
				raise KeyError("Unknown SIP-field name '%s'" % str(name))
			
			(slot, fmt) = self.sipFields[name]
			if (type(slot) == types.IntType) and ((type(value) == types.IntType) or (type(value) in types.StringTypes)):
				self._setField(slot, fmt, value)
			elif (type(slot) in (types.ListType, types.TupleType)) and (type(value) in (types.ListType, types.TupleType)):
				for (sl, val) in zip(slot, value):
					self._setField(sl, fmt, val)
			else:
				raise TypeError("Invalid SIP-field value-type for field '%s' (not int or string): '%s'" % (name, str(value)))
				
		self.setSlot(self[1], self.chksum8())
	
	def _getField(self, slot, fmt):
		"""Decode and return the value in the given slot or slot-pair.
		fmt is 'B' for byte or '>H' for big-endian 16-bit value
		"""
		if fmt == '>H':
			sz = 2
		else:
			sz = 1
		
		val_str = string.join(self.slots[slot:slot + sz], '')
		
		return struct.unpack(fmt, val_str)[0]
	
	def getField(self, name):
		"""Decode and return the value in the given field.
		See DMXSIPacket.setFields(...) for a list of field-names.
		In addition to the fields mentioned in DMXSIPacket.setFields(...), one can also get the
		'sipchksum' field. this returns the value stored in the 'SIP Checksum' slot (i.e. the last slot),
		it does NOT calculate the 'SIP Checksum' of the current SIPacket. See DMXSIPacket.chksum8()
		"""
		out = None
		if name in self.sipFields:
			(slot, fmt) = self.sipFields[name]
			if type(slot) == types.IntType:
				out = self._getField(slot, fmt)
			
			elif type(slot) in (types.ListType, types.TupleType):
				out = []
				for sl in slot:
					out.append(self._getField(sl, fmt))
					
		elif name == 'sipchksum':
			out = self[self[1]]
			
		return out
	
	def getFields(self):
		"""Return a dict with all possible field-names and the fields' decoded values
		"""
		out = {}
		for name in (self.sipFields.keys() + ['sipchksum']):
			out[name] = self.getField(name)
			
		return out
	
	def chksum8(self):
		"""Calculate & return the 8-bit additive SIP checksum.
		This method does NOT store the calculated checksum in the 'SIP Checksum' slot (i.e. the last slot)
		"""
		sum = 0
		fmt = 'B' * len(self.slots[:self[1]])
		for val in struct.unpack(fmt, str(self)[:self[1]]):
			sum = (sum + val) % 0x100
			
		return sum

	def setSize(self, size):
		"""Change the DMXSIPacket's size (i.e. nr of slots)
		'size' must be in range 24 - 255 inclusive
		"""
		if (size < 24) or (size > self.packetMaxSlots):
			raise ValueError("SIP size must be in range 24 - %d" % self.packetMaxSlots)
		
		# set current sipchksum field to 0
		self[self[1]] = 0
		# set new size. This also calculates new sipchksum in new last slot
		self.setFields({'size':size})
		# truncate slots
		self.slots = self.slots[:self[1] + 1]

	def getSize(self):
		"""Return the DMXSIPacket's size (i.e. nr of slots)
		"""
		return self.getField('size')
	
	def setCtrlBits(self, bits):
		"""Change the 'Control Bit' field
		Valid values are 0 - 3
		"""
		self.setFields({'ctrl':bits})
		
	def getCtrlBits(self):
		"""Return the 'Control Bit' field value
		"""
		return self.getField('ctrl')
	
	def setPPChksum(self, chksum):
		"""Change the 'Previous Packet's Checksum' field
		'chksum' is a 16-bit value (0 - 65535)
		"""
		self.setFields({'chksum':chksum})
		
	def getPPChksum(self):
		"""Return the 'Previous Packet's Checksum' field value
		"""
		return self.getField('chksum')
		
	def setSeqNr(self, seq):
		"""Change the 'SIP Sequence Number' field
		'seq' is an 8-bit value (0 - 255)
		"""
		self.setFields({'seq':seq})
		
	def getSeqNr(self):
		"""Return the 'SIP Sequence Number' field value
		"""
		return self.getField('seq')
	
	def setUniverse(self, universe):
		"""Change the 'DMX Universe Number' field
		Valid values are 0 - 255, with '0' meaning 'Multiple Universes not suported'
		"""
		self.setFields({'uni':universe})
		
	def getUniverse(self):
		"""Return the 'DMX Universe Number' field value
		"""
		return self.getField('uni')
	
	def setLevel(self, level):
		"""Change the 'DMX Processing Level' field (a.k.a. 'DMX Hop Count')
		This field's value is normally incremented by every DMX merger, router, etc. the Packet has passed.
		'level' is an 8-bit value (0 - 255)
		"""
		self.setFields({'level':level})
		
	def getLevel(self):
		"""Return the 'DMX Processing Level' field value
		"""
		return self.getField('level')
	
	def setVersion(self, version):
		"""Change the 'Software Version' field.
		This field is normally set by teh last DMX-device the apcket came from.
		Valid values are 0 - 255, with '0' meaning 'Not implemented'
		"""
		self.setFields({'version':version})
		
	def getVersion(self):
		"""Return the 'Software Version' field value
		"""
		return self.getField('version')
	
	def setLength(self, length):
		"""Change the 'Default NULL Packet Length' field (a.k.a. 'DMX Universe Size')
		The packet-length can be 'static' or 'dynamic', and either of those can be 'undefined' or 'defined':
		length-setting			meaning
		0x0000		(0)		static, length undefined (?)
		0x0001 - 0x0200 (1 - 512)	static, fixed length (1 - 512)
		0x8000		(32768)		dynamic, length undefined
		0x8001 - 0x8200	(32769 - 33280)	dynamic, length of last packet (1 - 512)
		"""
		self.setFields({'length':length})
		
	def getLength(self):
		"""Return the 'Default NULL Packet Length' field value
		"""
		return self.getField('length')
	
	def setCount(self, count):
		"""Change the 'Number of Packets transmitted since last SIP' field
		'count' is a 16-bit value (0 - 65535)
		"""
		self.setFields({'count':count})
		
	def getCount(self):
		"""Return the 'Number of Packets transmitted since last SIP' field
		"""
		return self.getField('count')
	
	def setMFIDs(self, mfids):
		"""Change the (list of) 'Device Manufacturer ID' fields
		'mfids' is a list/tuple of upto 5 16-bit values.
		A value of '0' means 'Manufacturer not defined'
		A value of 0xFFFF (65535) means 'Manufacturer waiting for official ID assignation'
		"""
		self.setFields({'mfids':mfids})
		
	def getMFIDs(self):
		"""Return the list of all 5 'Manufacturer ID' fields' values
		"""
		return self.getField('mfids')
	
	def setMFID(self, idx, mfid):
		"""Change the 'Manufacturer ID' field indicated by 'idx'
		'idx' must be in range 0 - 4
		A mfid of '0' means 'Manufacturer not defined'
		A mfid of 0xFFFF (65535) means 'Manufacturer waiting for official ID assignation'
		"""
		mfids = self.getField('mfids')
		mfids[idx] = mfid
		self.setFields({'mfids':mfids})

	def getMFID(self, idx):
		"""Return the value of the 'Manufacturer ID' field indicated by 'idx'
		'idx' must be in range 0 - 4
		"""
		mfids = self.getField('mfids')
		return mfids[idx]

	def getSIPChksum(self):
		"""Return the value of the 'SIP Checksum' field (the last slot)
		This method does NOT calculate the checksum, it only retrieves the value from the checksum-slot
		"""
		return self.getField('sipchksum')
	
	def testSIPChksum(self):
		"""Calculate the SIP checksum, and return 'True' if this checksum is equal to the checksum-value stored in the last slot.
		Returns 'False' if checksums do not match.
		"""
		return (self.getField('sipchksum') == self.chksum8())
	
	
def DMXReceive(in_str, ignore_checksum=False):
	"""Parse the given string and return a DMXPacket of the appropriate type
	(DMXPacket, DMXTextPacket, DMXTestPacket, DMXMFIDPacket or DMXSIPacket)
	The 'ignore_checksum' parameter is only relevant for a DMXSIPacket.
	(see DMXSIPacket.fromString(...))
	"""
	if type(in_str) not in types.StringTypes:
		raise DMXError("Invalid input-data type: %s" % type(in_str))
	
	if not len(in_str):
		return None
	
	startcode = struct.unpack('B', str(in_str)[0])[0]
	pkt = None
	
	if startcode == DMX512PacketNumbers['NULL']:
		pkt = DMXPacket()
		pkt.fromString(str(in_str))
	elif startcode == DMX512PacketNumbers['TEXT']:
		pkt = DMXTextPacket()
		pkt.fromString(str(in_str))
	elif startcode == DMX512PacketNumbers['TEST']:
		pkt = DMXTestPacket()
		pkt.fromString(str(in_str))
	elif startcode == DMX512PacketNumbers['MFID']:
		pkt = DMXMFIDPacket()
		pkt.fromString(str(in_str))
	elif startcode == DMX512PacketNumbers['SIP']:
		pkt = DMXSIPacket()
		pkt.fromString(str(in_str), ignore_checksum)
	elif startcode in range(DMX512PacketNumbers['TMP0'], DMX512PacketNumbers['TMP7'] + 1):
		pkt = DMXPacket()
		pkt.fromString(str(in_str))
	else:
		raise DMXError("Invalid startcode: '%s'" % str(startcode))

	return pkt