""" 
    This file is part of OpenHelbreath.

    OpenHelbreath is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenHelbreath is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenHelbreath.  If not, see <http://www.gnu.org/licenses/>.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import socket, os, sys, select, struct, time, re, random
from Enum import Enum
from threading import Thread, Semaphore, Event
from NetMessages import Packets
from GlobalDef import DEF, Account, Version
from Helpers import Callbacks
from Sockets import ServerSocket
from Database import DatabaseDriver
from collections import namedtuple

nozeros = lambda x: x[0:x.find('\x00')] if x.find('\x00')>-1 else x
fillzeros = lambda txt, count: (txt + ("\x00" * (count-len(txt))))[:count]
packet_format = lambda x: nozeros(x) if type(x) != int else x

class CGameServer(object):
	def __init__(self, id, sock):
		self.AliveResponseTime = time.time()
		self.GSID = id
		self.socket = sock
		self.MapName = []
		self.GameServerSocket = []
		self.Data = {}
		self.Config = {}
		self.IsRegistered = False
		self.Database = None

class CLoginServer(object):
	def __init__(self):
		"""
			Initializing login server
		"""
		self.MainSocket = None
		self.GateServerSocket = None
		self.ListenAddress = ""
		self.ListenPort = 2748
		self.GateServerPort = 0
		self.GameServer = {}
		self.ListenToAllAddresses = True
		self.ListenPortDefault = True
		self.PermittedAddress = []
		self.MaxTotalUsers = 1000
		self.WorldServerName = "WS1"
		self.Clients = []
		
	def DoInitialSetup(self):
		"""
			Loading main configuration, and initializing Database Driver
			(For now, its MySQL)
		"""
		if not self.ReadProgramConfigFile("LServer.cfg"):
			return False
		self.Database = DatabaseDriver()
		if not self.Database.Initialize():
			print "(!) DatabaseDriver initialization fails!"
			return False
		return True
		
	def GateServer_OnConnect(self, sender):
		"""
			Triggered when any client connects to Gate Server. Do nothing
		"""
		#print "(*) GateServer -> Accepted connection"
		pass
		
	def GateServer_OnDisconnected(self, sender):
		"""
			Triggered when any client disconnects from Gate Server.
			Check if Sender (ClientSocket class) is registered as sub-log-socket
			or Gate Server Socket. Unfortunatelly we can unregister sub-log-socket from
			registered Gate Server, but can't unload whole Game Server.
			Because Main GS socket disconnects at first.
			TODO: Inject Gate Server method in Sender's callbacks
		"""
		for i in self.GameServer.values():
			for j in i.GameServerSocket:
				if j == sender:
					print "(!) Lost connection to sub log socket on %s [GSID: %d] (!)" % (i.Data['ServerName'],i.GSID)
					i.GameServerSocket.remove(sender)
					return
		GS = self.SockToGS(sender)
		if GS != None:
			print "(*) GateServer %s -> Lost connection" % (GS.Data['ServerName'])
		else:
			print "Lost unknown connection on GateServer (not registered? hack attempt?)"	
		
	def GateServer_OnListen(self, sender):
		"""
			When socket is ready to accept connections
		"""
		print "(*) GateServer -> Server open"
		
	
	def SockToGS(self, sender):
		"""
			Finding GameServer by Sender's class
			Returns: Instance of CGameServer class
		"""
		for i in self.GameServer.values():
			if i.socket == sender:
				return i
		for i in self.GameServer.values():
			for j in i.GameServerSocket:
				if j == sender:
					return i
		
				
	def GateServer_OnReceive(self, sender, size):
		"""
			Triggered when any data is available on Sock's buffer
		"""
		buffer = sender.receive(size)
		try:
			format = '<Bh'
			header_size = struct.calcsize(format)
			if len(buffer) < header_size:
				raise Exception
			s = struct.unpack(format, buffer[:header_size])
			Header = namedtuple('Header', 'cKey dwSize')._make(s)
			buffer = buffer[header_size:]
		except:
			print "Except"
			sender.disconnect()
			return
			
		if Header.dwSize != size or size < 4 or Header.dwSize < 4:
			print "(!) %s Header.dwSize does not match buffer size. Hack!" % sender.address
			sender.disconnect()
			return

		if Header.cKey > 0:
			Decode = lambda buffer, dwSize, cKey: "".join(map(lambda n: (lambda asdf: chr(asdf & 255))((ord(buffer[n]) ^ (cKey ^ (dwSize - n))) - (n ^ cKey)), range(len(buffer))))
			buffer = Decode(buffer, Header.dwSize-3, Header.cKey)
				
		MsgID = struct.unpack('<L', buffer[:4])[0]
		buffer = buffer[4:]
				
		if MsgID == Packets.MSGID_REQUEST_REGISTERGAMESERVER:
			self.RegisterGameServer(sender, buffer)
		elif MsgID == Packets.MSGID_REQUEST_REGISTERGAMESERVERSOCKET:
			self.RegisterGameServerSocket(sender, buffer)
		elif MsgID == Packets.MSGID_GAMESERVERALIVE:
			GS = self.SockToGS(sender)
			if GS != None:
				self.GameServerAliveHandler(GS, buffer)
			else:
				print "MSGID_GAMESERVERALIVE ON UNREGISTERED SOCKET. PLEASE RESTART! HACK?"
		elif MsgID == Packets.MSGID_REQUEST_PLAYERDATA:
			GS = self.SockToGS(sender)
			if GS != None:
				self.ProcessRequestPlayerData(sender, buffer, GS)
		elif MsgID in [Packets.MSGID_GAMEMASTERLOG, Packets.MSGID_ITEMLOG]:
			print buffer[2:]
		elif MsgID == Packets.MSGID_SERVERSTOCKMSG:
			GS = self.SockToGS(sender)
			print "(!!!!!) StockMSG %s" % repr(buffer)
			if GS != None:
				self.ServerStockMsgHandler(GS, buffer);
		elif MsgID == Packets.MSGID_REQUEST_SAVEPLAYERDATALOGOUT:
			GS = self.SockToGS(sender)
			if GS != None:
				print "(!) Save player data..."
				self.SavePlayerData(buffer,GS)
		else:
			if MsgID in Packets:
				print "(!) Gate Server -> Packet MsgID: %s (0x%08X) %db * %s" % (Packets.reverse_lookup_without_mask(MsgID), MsgID, len(buffer), repr(buffer))
			else:
				print "(!) Gate Server -> Unknown packet MsgID: (0x%08X) %db * %s" % (MsgID, len(buffer), repr(buffer))
				
	def GateServer_OnClose(self, sender, size):
		"""
			Triggered when Gate Server thread is closed
		"""
		print "(*) GateServer -> Server close"
		
	def InitServer(self):
		"""
			Load all HG configs and create sockets
			Returns: True if OK, False if fails
		"""
		if not self.bReadAllConfig():
			return False
		print "(*) Done!"
		
		GateServerCB = {'onConnected': self.GateServer_OnConnect,
						'onDisconnected': self.GateServer_OnDisconnected,
						'onListen': self.GateServer_OnListen,
						'onReceive': self.GateServer_OnReceive,
						'onClose': self.GateServer_OnClose}

		MainSocketCB = {'onConnected': self.MainSocket_OnConnect,
						'onDisconnected': self.MainSocket_OnDisconnected,
						'onListen': self.MainSocket_OnListen,
						'onReceive': self.MainSocket_OnReceive,
						'onClose': self.MainSocket_OnClose}

		if self.ListenToAllAddresses:
			print "(!) permitted-address line not found in LServer.cfg. Server will be listening to all IPs!"

		if self.ListenPortDefault:
			print "(*) login-server-port line not found in LServer.cfg. Server will use port %d" % self.ListenPort

		self.GateServerSocket = ServerSocket((self.ListenAddress, self.GateServerPort), GateServerCB)
		self.GateServerSocket.start()
		print "(*) Gate server successfully started!"

		self.MainSocket = ServerSocket((self.ListenAddress, self.ListenPort), MainSocketCB)
		self.MainSocket.start()
		print "(*) Login server sucessfully started!"
		
		return True
			
	def bReadAllConfig(self):
		"""
			Reading HG cfgs in order
		"""
		Files = ["Item.cfg", "Item2.cfg", "Item3.cfg", "BuildItem.cfg",
				"DupItemID.cfg", "Magic.cfg", "noticement.txt", 
				"NPC.cfg", "Potion.cfg", "Quest.cfg", "Skill.cfg",
				"AdminSettings.cfg", "Settings.cfg"]
		self.Config = {}
		for n in Files:
			if not self.ReadConfig("Config/%s" % n):
				return False
		return True
		
	def ReadProgramConfigFile(self, cFn):
		"""
			Parse main configuration file
		"""
		if not os.path.exists(cFn) and not os.path.isfile(cFn):
			print "(!) Cannot open configuration file."
			return False
			
		reg = re.compile('[a-zA-Z]')
		fin = open(cFn, 'r')
		try:
			for line in fin:
				if reg.match(line) == None:
					continue
					
				token = filter(lambda l: True if type(l) == int else (l.strip() != ""), map(lambda x: (lambda y: int(y) if y.isdigit() else y)(x.strip().replace('\t',' ').replace('\r', '').replace('\n','')), line.split('=')))
				
				if len(token)<2:
					continue
					
				if token[0] == "login-server-address":
					self.ListenAddress = token[1]
					print "(*) Login server address : %s" % (self.ListenAddress)
					
				if token[0] == "login-server-port":
					self.ListenPort = token[1]
					print "(*) Login server port : %d" % (self.ListenPort)
					if self.ListenPortDefault:
						self.ListenPortDefault = False
					
				if token[0] == "gate-server-port":
					self.GateServerPort = token[1]
					print "(*) Gate Server port : %d" % (self.GateServerPort)
					
				if token[0] == "permitted-address":
					self.PermittedAddress += [token[1]]
					print "(*) IP [%s] added to permitted addresses list!" % (token[1])
					if self.ListenToAllAddresses:
						self.ListenToAllAddresses = False
						
				if token[0] == "max-total-users":
					self.MaxTotalUsers = token[1]
					print "(*) Max total users allowed on server : %d" % self.MaxTotalUsers
					
				if token[0] == "world-server-name":
					self.WorldServerName = token[1]
					print "(*) World Server Name : %s" % self.WorldServerName
		finally:
			fin.close()
		return True
			
	def ReadConfig(self, FileName):
		"""
			Read contents of file to Config dict
		"""
		if not os.path.exists(FileName) and not os.path.isfile(FileName):
			print "(!) Cannot open configuration file [%s]." % FileName
			return False
		key = FileName.split('/')[-1].split(".")[0]
		fin = open(FileName,'r')
		print "(*) Reading configuration file [%s] -> {'%s'}..." % (FileName, key)
		try:
			self.Config[key] = fin.read()
		finally:
			fin.close()
		return True
		
	def RegisterGameServer(self, sender, data):
		"""
			Registering new Game Server
		"""
		(ok, GSID, GS) = self.TryRegisterGameServer(sender, data)
		PacketID = Packets.DEF_MSGTYPE_REJECT if ok == False else Packets.DEF_MSGTYPE_CONFIRM
		SendData = struct.pack('L2h', Packets.MSGID_RESPONSE_REGISTERGAMESERVER, PacketID, GSID)
		self.SendMsgToGS(GS, SendData)
		print "(*) Game Server registered at ID[%u]-[%u]." % (GSID, GS.Data['InternalID'])
		
	def FindNewGSID(self):
		"""
			Finding new GameServer
			TODO: Convert to lambda
		"""
		m = 1
		for i in self.GameServer:
			if i > m:
				m = i
		return m
		
	def TryRegisterGameServer(self, sender, data):
		"""
			Read data from buffer and register HG
			TODO: Detect more security vuln
			Returns: Tuple ( OK/Fail, GS_ID/-1, CGameServer instance/None)
		"""
		global nozeros
		Read = {}
		Request = struct.unpack('h', data[:2])[0]
		if Request != Packets.DEF_LOGRESMSGTYPE_CONFIRM:
			print "Unknown Register Game Server Packet ID"
			return (False, -1, None)
		data = data[2:]
		Read['ServerName'] = nozeros(data[:10])
		Read['ServerIP'] = nozeros(data[10:26])
		Read['ServerPort'] = struct.unpack('h', data[26:28])[0]
		Read['ReceivedConfig'] = ord(data[28])
		Read['NumberOfMaps'] = ord(data[29])
		if Read['NumberOfMaps'] == 0:
			return (False, -1, None)
		Read['InternalID'] = struct.unpack('h', data[30:32])[0] #ord(data[30])
		
		if sender.address not in self.PermittedAddress and not self.ListenToAllAddresses:
			print "(!) %s is not in permitted address list and tries to register Game Server!"
			return (False, -1, None)
		
		NGSID = self.FindNewGSID()
		print Read
		GS = CGameServer(NGSID, sender)
		GS.Data = Read
		print "(*) Maps registered:"
		data = data[32:]
		while len(data)>0:
			map_name = nozeros(data[:11])
			GS.MapName += [map_name]
			data = data[11:]
			print "- %s" % (map_name)
		if not GS.Data['ReceivedConfig']:
			self.SendConfigToGS(GS)
		self.GameServer[NGSID] = GS
		return (True, NGSID, GS)
		
	def SendMsgToGS(self, GS, data):
		"""
			Sending data to Game Server
		"""
		cKey = 0
		dwSize = len(data)+3
		Buffer = chr(cKey) + struct.pack('h', dwSize) + data
		if cKey > 0:
			for i in range(dwSize):
				Buffer[3+i] = chr(ord(Buffer[3+i]) + (i ^ cKey))
				Buffer[3+i] = chr(ord(Buffer[3+i]) ^ (cKey ^ (dwSize - i)))
		GS.socket.client.send(Buffer)
		
	def SendConfigToGS(self, GS):
		"""
			Send config to Game Server. Much shorter than in Arye's src!
		"""
		Order = (
					(Packets.MSGID_ITEMCONFIGURATIONCONTENTS, 'Item'),
					(Packets.MSGID_ITEMCONFIGURATIONCONTENTS, 'Item2'),
					(Packets.MSGID_ITEMCONFIGURATIONCONTENTS, 'Item3'),
					(Packets.MSGID_BUILDITEMCONFIGURATIONCONTENTS, 'BuildItem'),
					(Packets.MSGID_DUPITEMIDFILECONTENTS, 'DupItemID'),
					(Packets.MSGID_MAGICCONFIGURATIONCONTENTS, 'Magic'),
					(Packets.MSGID_NOTICEMENTFILECONTENTS, 'noticement'),
					(Packets.MSGID_NPCCONFIGURATIONCONTENTS, 'NPC'),
					(Packets.MSGID_PORTIONCONFIGURATIONCONTENTS, 'Potion'),
					(Packets.MSGID_QUESTCONFIGURATIONCONTENTS, 'Quest'),
					(Packets.MSGID_SKILLCONFIGURATIONCONTENTS, 'Skill'), 
					(Packets.MSGID_ADMINSETTINGSCONFIGURATIONCONTENTS, 'AdminSettings'),
					(Packets.MSGID_SETTINGSCONFIGURATIONCONTENTS, 'Settings')
				)
				
		for packet_id, key in Order:
			if not key in self.Config:
				print "%s config not loaded!" % key
				break
			SendCfgData = struct.pack('Lh', packet_id, 0) + self.Config[key]
			self.SendMsgToGS(GS, SendCfgData)

	def RegisterGameServerSocket(self, sender, data):
		"""
			Here we are adding socket to Game Server
		"""
		GSID = ord(data[0])
		print "(*) Trying to register socket on GS[%d]." % GSID
		if not GSID in self.GameServer:
			print "(!) GSID is not registered!"
			return False
		self.GameServer[GSID].GameServerSocket += [sender]
		print "(*) Registered Socket(%d) GSID(%d) ServerName(%s)" % (len(self.GameServer[GSID].GameServerSocket), GSID, self.GameServer[GSID].Data['ServerName'])
		if len(self.GameServer[GSID].GameServerSocket) == DEF.MAXSOCKETSPERSERVER:
			self.GameServer[GSID].IsRegistered = True
			print "(*) Gameserver(%s) registered!" % (self.GameServer[GSID].Data['ServerName'])
			print
			
	def GameServerAliveHandler(self, GS, data):
		"""
			Game Server is sending us PING every 3 seconds.
			It contains MsgType (DEF_MSGTYPE_CONFIRM) and Total players connected
			Original Arye's src doesnt handle it very well
			TODO: Disconnecting not responding game servers
		"""
		if len(data)<4:
			print "GameServerAliveHandler: Size mismatch!"
			return	
		(MsgType, TotalPlayers) = struct.unpack('hh', data[:4])
		if MsgType == Packets.DEF_MSGTYPE_CONFIRM:
			GS.AliveResponseTime = time.time()
			
	def MainSocket_OnConnect(self, sender):
		print "(*) MainSocket-> Client accepted [%s]" % sender.address
		
	def MainSocket_OnDisconnected(self, sender):
		print "(*) MainSocket -> Client disconnected"
		
	def MainSocket_OnListen(self, sender):
		print "(*) MainSocket -> Server open"
		
	def MainSocket_OnReceive(self, sender, size):
		print "(*) MainSocket -> Received %d bytes" % size
		buffer = sender.receive(size)
		try:
			format = '<Bh'
			header_size = struct.calcsize(format)
			if len(buffer) < header_size:
				raise Exception
			s = struct.unpack(format, buffer[:header_size])
			Header = namedtuple('Header', 'cKey dwSize')._make(s)
			buffer = buffer[header_size:]
		except:
			print "Except"
			sender.disconnect()
			return
			
		if Header.dwSize != size or size < 4 or Header.dwSize < 4:
			print "(!) %s Header.dwSize does not match buffer size. Hack!" % sender.address
			sender.disconnect()
			return

		if Header.cKey > 0:
			Decode = lambda buffer, dwSize, cKey: "".join(map(lambda n: (lambda asdf: chr(asdf & 255))((ord(buffer[n]) ^ (cKey ^ (dwSize - n))) - (n ^ cKey)), range(len(buffer))))
			buffer = Decode(buffer, Header.dwSize-3, Header.cKey)
				
		MsgID = struct.unpack('<L', buffer[:4])[0]
		buffer = buffer[4:]
		
		if MsgID == Packets.MSGID_REQUEST_LOGIN:
			self.ProcessClientLogin(sender, buffer)
		elif MsgID == Packets.MSGID_REQUEST_CHANGEPASSWORD:
			self.ChangePassword(sender, buffer)
		elif MsgID == Packets.MSGID_REQUEST_CREATENEWCHARACTER:
			self.CreateNewCharacter(sender, buffer)
		elif MsgID == Packets.MSGID_REQUEST_DELETECHARACTER:
			self.DeleteCharacter(sender, buffer)
		elif MsgID == Packets.MSGID_REQUEST_CREATENEWACCOUNT:
			self.CreateNewAccount(sender, buffer)
		elif MsgID == Packets.MSGID_REQUEST_ENTERGAME:
			self.ProcessClientRequestEnterGame(sender, buffer)
		else:
			if MsgID in Packets:
				print "Packet MsgID: %s (0x%08X) %db * %s" % (Packets.reverse_lookup_without_mask(MsgID), MsgID, len(buffer), repr(buffer))
			else:
				print "Unknown packet MsgID: (0x%08X) %db * %s" % (MsgID, len(buffer), repr(buffer))
			#sender.disconnect()
			
	def MainSocket_OnClose(self, sender):
		pass
		
	def SendMsgToClient(self, Sock, data, cKey = -1):
		"""
			Sending data to Client
		"""
		dwSize = len(data)+3
		buffer = data[:]
		if cKey == -1:
			cKey = random.randint(0, 255)
		if cKey > 0:
			buffer = map(ord, buffer)#list(data)
			for i in range(len(buffer)):#range(dwSize):
				buffer[i] = buffer[i] + (i ^ cKey)
				buffer[i] = buffer[i] ^ (cKey ^ (len(buffer) - i))
			buffer = "".join(map(lambda x: chr(x & 255) , buffer))
		buffer = chr(cKey) + struct.pack('h', len(buffer)+3) + buffer
		Sock.client.send(buffer)
		
	def ProcessClientLogin(self, sender, buffer):
		"""
			Processing Client Login
			Improvements from Arye's server:
			+ BlockDate is now used properly
			+ Check if client is trying to log on correct WS.
		"""
		try:
			format = '<h10s10s30s'
			format410 = '<h10s10s30sI32s32s32s'
			if len(buffer) == struct.calcsize(format):
				s = map(packet_format, struct.unpack(format, buffer))
				Packet = namedtuple('Packet', 'MsgType AccountName AccountPassword WS')._make(s)
			elif len(buffer) == struct.calcsize(format410):
				s = map(packet_format, struct.unpack(format410, buffer))
				Packet = namedtuple('Packet', 'MsgType AccountName AccountPassword WS Unk1int Unk2str Unk3str Unk4str')._make(s)
				print "(!) %s - %s request login with 4.10 client!" % (sender.address, Packet.AccountName)
			else:
				s = map(packet_format, struct.unpack(format, buffer[:struct.calcsize(format)]))
				Packet = namedtuple('Packet', 'MsgType AccountName AccountPassword WS')._make(s)
		except:
			SendData = struct.pack('<Lh3iB', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_REJECT, 0, 0, 0, 1)
			self.SendMsgToClient(sender, SendData)
			return
			
		if Packet.WS != self.WorldServerName:
			print "(!) Player tries to enter unknown World Server : %s" % Packet.WS
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NOTEXISTINGWORLDSERVER)
			self.SendMsgToClient(sender, SendData)
			return
			
		OK = self.Database.CheckAccountLogin(Packet.AccountName, Packet.AccountPassword)
		if OK[0] == Account.OK:
			print "(*) Login OK: %s" % Packet.AccountName
			SendData = struct.pack('<L3hB12s', Packets.MSGID_RESPONSE_LOG, Packets.DEF_MSGTYPE_CONFIRM,
												Version.UPPER, Version.LOWER,
												0, #account status
												'') #dates, converted to 12 * \0x00
			ChLst = self.GetCharList(Packet.AccountName, Packet.AccountPassword)
			SendData += ChLst
			self.SendMsgToClient(sender, SendData)
			
		elif OK[0] == Account.WRONGPASS:
			print "(!) Wrong password: Account[ %s ] - Correct Password[ %s ] - Password received[ %s ]" % (Packet.AccountName, OK[2], OK[1])
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_PASSWORDMISMATCH)
			self.SendMsgToClient(sender, SendData)
			
		elif OK[0] == Account.NOTEXISTS:
			print "(!) Account does not exists: %s" % Packet.AccountName
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NOTEXISTINGACCOUNT)
			self.SendMsgToClient(sender, SendData)
			
		elif OK[0] == Account.BLOCKED:
			print "(!) Account %s blocked until %d-%d-%d and tries to login!" % (Read['AccountName'], OK[1], OK[2], OK[3])
			SendData = struct.pack('<Lh3i', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_REJECT, 
												OK[1], OK[2], OK[3], #Y-m-d
												0) #Account Status
			self.SendMsgToClient(sender, SendData)
			
	def ChangePassword(self, sender, buffer):
		global packet_format
		try:
			format = '<h10s10s10s10s'
			if len(buffer) != struct.calcsize(format):
				raise Exception
			s = map(packet_format, struct.unpack(format, buffer))
			Packet = namedtuple('Packet', 'MsgType Login Password NewPass1 NewPass2')._make(s)
		except:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERFAILED)
			self.SendMsgToClient(sender, SendData)
			return

		OK = self.Database.CheckAccountLogin(Packet.Login, Packet.Password)
		
		if Packet.NewPass1 != Packet.NewPass2 or len(Packet.NewPass1) < 8 or len(Packet.NewPass2) < 8:
			print "(!) Password changed on account %s (%s -> %s) FAIL! (Password confirmation)" % (Packet.Login, Packet.Password, Packet.NewPass1)
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_CHANGEPASSWORD, Packets.DEF_LOGRESMSGTYPE_PASSWORDCHANGEFAIL)
			self.SendMsgToClient(sender, SendData)
			return
			
		if OK[0] == Account.WRONGPASS:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_CHANGEPASSWORD, Packets.DEF_LOGRESMSGTYPE_PASSWORDMISMATCH)
			self.SendMsgToClient(sender, SendData)
			print "(!) Password changed on account %s (%s -> %s) FAIL! (Password mismatch)" % (Packet.Login, Packet.Password, Packet.NewPass1)
			return
			
		if OK[0] != Account.OK:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_CHANGEPASSWORD, Packets.DEF_LOGRESMSGTYPE_PASSWORDCHANGEFAIL)
			self.SendMsgToClient(sender, SendData)
			print "(!) Password changed on account %s (%s -> %s) FAIL! (%s)" % (Packet.Login, Packet.Password, Packet.NewPass1, Account.reverse_lookup_without_mask(OK[0]))
			return
			
		if self.Database.ChangePassword(Packet.Login, Packet.Password, Packet.NewPass1):
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_CHANGEPASSWORD, Packets.DEF_LOGRESMSGTYPE_PASSWORDCHANGESUCCESS)
			self.SendMsgToClient(sender, SendData)
			print "(*) Password changed on account %s (%s -> %s) SUCCESS!" % (Packet.Login, Packet.Password, Packet.NewPass1)
		else:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_CHANGEPASSWORD, Packets.DEF_LOGRESMSGTYPE_PASSWORDCHANGEFAIL)
			self.SendMsgToClient(sender, SendData)
			print "(!) Password changed on account %s (%s -> %s) FAIL! (Database failed)" % (Packet.Login, Packet.Password, Packet.NewPass1)
	
	def CreateNewCharacter(self, sender, buffer):
		global packet_format
		try:
			format = '<h10s10s10s30s11B'
			if len(buffer) != struct.calcsize(format):
				raise Exception
			s = map(packet_format, struct.unpack(format, buffer))
			Packet = namedtuple('Packet', 'MsgType PlayerName AccountName AccountPassword WS Gender SkinCol HairStyle HairCol UnderCol Str Vit Dex Int Mag Agi')._make(s)
		except:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERFAILED)
			self.SendMsgToClient(sender, SendData)
			return
			
		OK = self.Database.CheckAccountLogin(Packet.AccountName, Packet.AccountPassword)
		if OK[0] != Account.OK or Packet.PlayerName == "" or Packet.WS != self.WorldServerName:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERFAILED)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create new character -> Wrong account data on creating new character!"
			return
			
		if self.Database.CharacterExists(Packet.PlayerName):
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_ALREADYEXISTINGCHARACTER)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create new character -> Character %s already exists." % Packet.PlayerName
			return
			
		CharList = self.Database.GetAccountCharacterList(Packet.AccountName, Packet.AccountPassword)
		Stat = [getattr(Packet, x) for x in ['Str','Vit','Dex','Int','Mag','Agi']]
		print Stat
		if filter(lambda x: x not in [10,11,12,13,14], Stat) < 6: #test if requested Stats are not in valid values
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERFAILED)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create new character -> Stat values not in [10, 11, 12, 13, 14]"
			return
		
		if reduce(lambda a,b: a+b, Stat) != 70: #if stats count does not compare 70
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERFAILED)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create new character -> Stat values %d/70!" % (reduce(lambda a,b: a+b, Stat))
			return
			
		if len(CharList) > 4: #more than 4 chars?
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERFAILED)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create new character -> Account tries make to more than 4 characters"
			return
		
		if not self.Database.CreateNewCharacter(Packet):
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERFAILED)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create new character -> Create new character failed at CreateNewCharacter!"
		else:
			SendData = struct.pack('<Lh10s',Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWCHARACTERCREATED,
											Packet.PlayerName)
			SendData += self.GetCharList(Packet.AccountName, Packet.AccountPassword)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create new character -> Create new character success on account %s [CharName: %s ]!" % (Packet.AccountName, Packet.PlayerName)

	def GetCharList(self, account_name, account_password):
		global fillzeros
		CharList = self.Database.GetAccountCharacterList(account_name, account_password)
		Buffer = chr(len(CharList))		
		for Char in CharList:
			Tmp = struct.pack('<10sB6h2i6h12s10s',
							Char['char_name'],
							1, #wtf?
							Char['Appr1'], Char['Appr2'], Char['Appr3'], Char['Appr4'],
							Char['Gender'],
							Char['Skin'],
							Char['Level'],
							Char['Exp'],
							Char['Strength'], Char['Vitality'], Char['Dexterity'], Char['Intelligence'], Char['Magic'], Char['Agility'],
							"", #will be converted to 12 * \0x00 -> Logout date
							Char['MapLoc'])
			Buffer += Tmp
		return Buffer
		
	def DeleteCharacter(self, sender, buffer):
		global packet_format
		try:
			format = '<h10s10s10s30s'
			if len(buffer) != struct.calcsize(format):
				raise Exception
			s = map(packet_format, struct.unpack(format, buffer))
			Packet = namedtuple('Packet', 'MsgType CharName AccountName AccountPassword WS')._make(s)
		except:
			print "Exception"
			SendData = struct.pack('Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NOTEXISTINGCHARACTER)
			self.SendMsgToClient(sender, SendData)
			return
			
		if Packet.WS != self.WorldServerName or not self.Database.DeleteCharacter(Packet.AccountName, Packet.AccountPassword, Packet.CharName):
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NOTEXISTINGCHARACTER)
			self.SendMsgToClient(sender, SendData)
			return

		SendData = struct.pack('<LhB', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_CHARACTERDELETED, 1)
		SendData += self.GetCharList(Packet.AccountName, Packet.AccountPassword)
		self.SendMsgToClient(sender, SendData)
		
	def CreateNewAccount(self, sender, buffer):
		global nozeros
		global packet_format
		try:
			format = '<h10s10s50s10s10si2h17s28s45s20s50s'
			if len(buffer) != struct.calcsize(format):
				raise Exception
			s = map(packet_format, struct.unpack(format, buffer))
			Packet = namedtuple('Packet', 'MsgType AccountName AccountPassword Mail Gender AccountAge Unk1 Unk2 Unk3 AccountCountry AccountSSN AccountQuiz AccountAnswer CmdLine')._make(s)
		except:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWACCOUNTFAILED)
			self.SendMsgToClient(sender, SendData)
			return
		
		OK = self.Database.CreateNewAccount(Packet.AccountName, Packet.AccountPassword, Packet.Mail, Packet.AccountQuiz, Packet.AccountAnswer, sender.address)
		if OK == Account.OK:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWACCOUNTCREATED)
			self.SendMsgToClient(sender, SendData)
			print "(*) Create account success [ %s/%s ]." % (Packet.AccountName, Packet.Mail)
		elif OK == Account.FAIL:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_NEWACCOUNTFAILED)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create account fails [ %s ]. Unknown error occured!" % Packet.AccountName
		elif OK == Account.EXISTS:
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_LOG, Packets.DEF_LOGRESMSGTYPE_ALREADYEXISTINGACCOUNT)
			self.SendMsgToClient(sender, SendData)
			print "(!) Create account fails [ %s ]. Account already exists" % Packet.AccountName

	def ProcessClientRequestEnterGame(self, sender, buffer):
		try:
			global packet_format
			format = '<h10s10s10s10si30s120s'
			if len(buffer) != struct.calcsize(format):
				print "%d/%d" % (len(buffer), struct.calcsize(format))
				raise Exception
			s = map(packet_format, struct.unpack(format, buffer))
			Packet = namedtuple('Packet', 'MsgType PlayerName MapName AccountName AccountPassword Level WS CmdLine')._make(s)
		except:
			SendData = struct.pack('<LhB', Packets.MSGID_RESPONSE_ENTERGAME, Packets.DEF_ENTERGAMERESTYPE_REJECT, Packets.DEF_REJECTTYPE_DATADIFFERENCE)
			self.SendMsgToClient(sender, SendData)
			return
		
		if Packet.WS != self.WorldServerName:
			print "(!) Player tries to enter game with unknown World Server : %s" % Packet.WS
			SendData = struct.pack('<LhB', Packets.MSGID_RESPONSE_ENTERGAME, Packets.DEF_ENTERGAMERESTYPE_REJECT, Packets.DEF_REJECTTYPE_DATADIFFERENCE)
			self.SendMsgToClient(sender, SendData)
			return
			
		OK = self.Database.CheckAccountLogin(Packet.AccountName, Packet.AccountPassword)
		if OK[0] != Account.OK:
			SendData = struct.pack('<LhB', Packets.MSGID_RESPONSE_ENTERGAME, Packets.DEF_ENTERGAMERESTYPE_REJECT, Packets.DEF_REJECTTYPE_DATADIFFERENCE)
			self.SendMsgToClient(sender, SendData)
			return
		
		Ch = self.Database.GetAccountCharacterList(Packet.AccountName, Packet.AccountPassword)
		Found = False
		for C in Ch:
			if C['char_name'] == Packet.PlayerName:
				Found = True
		if Found:
			GS = self.IsMapAvailable(Packet.MapName)
			if GS == False:
				print "(!) Player %s is stuck at %s !" % (Packet.PlayerName, Packet.MapName)
				SendData = struct.pack('<LhB', Packets.MSGID_RESPONSE_ENTERGAME, Packets.DEF_ENTERGAMERESTYPE_REJECT, Packets.DEF_REJECTTYPE_GAMESERVERNOTONLINE)
				self.SendMsgToClient(sender, SendData)
			else:
				if Packet.MsgType == Packets.DEF_ENTERGAMEMSGTYPE_NEW:
					self.Clients += [{
										'AccountName': Packet.AccountName,
										'AccountPassword': Packet.AccountPassword,
										'CharName': Packet.PlayerName,
										'Level': Packet.Level,
										'ClientIP': sender.address,
										'ID': GS['GSID']}]
						
					SendData = struct.pack('<Lh16sh20s', Packets.MSGID_RESPONSE_ENTERGAME, Packets.DEF_ENTERGAMERESTYPE_CONFIRM, 
															GS['IP'], GS['Port'],
															"") #ServerName?
					print "Client enter game : %s" % Packet.PlayerName
					self.SendMsgToClient(sender, SendData)
					
		else:
			SendData = struct.pack('<LhB', Packets.MSGID_RESPONSE_ENTERGAME, Packets.DEF_ENTERGAMERESTYPE_REJECT, Packets.DEF_REJECTTYPE_DATADIFFERENCE)
			self.SendMsgToClient(sender, SendData)
			
	def IsMapAvailable(self, MapName):
		for GS in self.GameServer.values():
			if MapName in GS.MapName:
				return {'IP':GS.Data['ServerIP'], 'Port': GS.Data['ServerPort'], 'GSID': GS.GSID}
		return False
		
	def IsAccountInUse(self, AccountName):
		for C in self.Clients:
			if C['AccountName'] == AccountName:
				return True
		return False

	def ProcessRequestPlayerData(self, sender, buffer, GS):
		print "Process request player data..."
		try:
			global packet_format
			format = '<h10s10s10s15sB'
			if len(buffer) != struct.calcsize(format):
				print "(!) RequestPlayerData size mismatch!"
				raise Exception				
			s = map(packet_format, struct.unpack(format, buffer))
			Packet = namedtuple('Packet', 'MsgType CharName AccountName AccountPassword Address AccountStatus')._make(s)
		except:
			SendData = SendData = struct.pack('<Lh10s', Packets.MSGID_RESPONSE_PLAYERDATA, Packets.DEF_LOGRESMSGTYPE_REJECT, "")
			self.SendMsgToGS(GS, SendData)
			return
		Found = False
		for C in self.Clients:
			if C['CharName'] == Packet.CharName and C['AccountName'] == Packet.AccountName and C['AccountPassword'] == Packet.AccountPassword:
				if C['ClientIP'] != "127.0.0.1" and C['ClientIP'] != Packet.Address:
					print "IP SIE NIE ZGADZA"
				else:
					Found = True
					break
				
		if not Found:
			print "(!) HG server is requesting not logged player! HACK!"
			SendData = struct.pack('<Lh10s', Packets.MSGID_RESPONSE_PLAYERDATA, Packets.DEF_LOGRESMSGTYPE_REJECT, Packet.CharName)
			self.SendMsgToGS(GS, SendData)
		else:
			print "GetCharacterInfo"
			SendData = struct.pack('<Lh', Packets.MSGID_RESPONSE_PLAYERDATA, Packets.DEF_LOGRESMSGTYPE_CONFIRM)
			SendData += self.GetCharacterInfo(Packet.AccountName, Packet.AccountPassword, Packet.CharName)
			print "SendMsgToGS"
			self.SendMsgToGS(GS, SendData)

	def GetCharacterInfo(self, AccountName, AccountPassword, CharName):
		OK = self.Database.GetCharacter(AccountName, AccountPassword, CharName)
		if OK == False:
			"OK == False"
			return
		print "GetCharacterInfo..."
		Ch = OK['Content']

		Data = struct.pack('10s', CharName)
		Data += struct.pack('B', int("0")) #Account Status - outdated
		Data += struct.pack('B', int("0")) #Guild Status - outdated
		Data += struct.pack('10s', Ch['MapLoc'])
		Data += struct.pack('hh', Ch['LocX'], Ch['LocY'])
		Data += struct.pack('B', Ch['Gender'])
		Data += struct.pack('B', Ch['Skin'])
		Data += struct.pack('B', Ch['HairStyle'])
		Data += struct.pack('B', Ch['HairColor'])
		Data += struct.pack('B', Ch['Underwear'])
		Data += struct.pack('20s', Ch['GuildName'])
		#Data += struct.pack('b', Ch['GuildRank'])
		Data += chr(Ch['GuildRank'] & 255)
		Data += struct.pack('i', Ch['HP'])
		Data += struct.pack('h', Ch['Level'])
		Data += struct.pack('B', Ch['Strength'])
		Data += struct.pack('B', Ch['Vitality'])
		Data += struct.pack('B', Ch['Dexterity'])
		Data += struct.pack('B', Ch['Intelligence'])
		Data += struct.pack('B', Ch['Magic'])
		Data += struct.pack('B', Ch['Agility'])
		Data += struct.pack('B', Ch['Luck'])
		Data += struct.pack('i', Ch['Exp'])
		Data += struct.pack('100s', Ch['MagicMastery'])
		
		for each in OK['Skill']:
			for key, value in each.iteritems():
				if key == "SkillMastery":
					Data += struct.pack('B', value)
					
		Data += struct.pack('10s', Ch['Nation'])
		Data += struct.pack('i', Ch['MP'])
		Data += struct.pack('i', Ch['SP'])
		Data += struct.pack('B', int("0")) # LU-pool - outdated
		Data += struct.pack('i', Ch['EK'])
		Data += struct.pack('i', Ch['PK'])
		Data += struct.pack('i', Ch['RewardGold'])
		
		for each in OK['Skill']:
			for key, value in each.iteritems():
				if key == "SkillSSN":
					Data += struct.pack('i', value)
					
		Data += struct.pack('i', int("0")) #spacer
		Data += struct.pack('B', Ch['Hunger'])
		Data += struct.pack('B', Ch['AdminLevel'])
		Data += struct.pack('i', Ch['LeftShutupTime'])
		Data += struct.pack('i', Ch['LeftPopTime'])
		Data += struct.pack('i', Ch['Popularity'])		
		Data += struct.pack('i', Ch['GuildID']) # changed to I (unsigned int) previously h (short)-
		#Data += struct.pack('b', Ch['DownSkillID'])
		Data += chr(Ch['DownSkillID'] & 255)
		Data += struct.pack('i', Ch['CharID'])
		Data += struct.pack('i', Ch['ID1'])
		Data += struct.pack('i', Ch['ID2'])
		Data += struct.pack('i', Ch['ID3'])
		Data += struct.pack('20s', str(Ch['BlockDate']) if Ch['BlockDate'] != None else "0000-00-00 00:00:00")
		Data += struct.pack('h', Ch['QuestNum'])
		Data += struct.pack('h', Ch['QuestCount'])
		Data += struct.pack('h', Ch['QuestRewType'])
		Data += struct.pack('i', Ch['QuestRewAmmount'])
		Data += struct.pack('i', Ch['Contribution'])
		Data += struct.pack('i', Ch['QuestID'])
		Data += struct.pack('B', Ch['QuestCompleted'])
		Data += struct.pack('i', Ch['LeftForceRecallTime'])
		Data += struct.pack('i', Ch['LeftFirmStaminarTime'])
		Data += struct.pack('i', Ch['EventID'])
		Data += struct.pack('h', Ch['LeftSAC'])
		Data += struct.pack('B', Ch['FightNum'])
		Data += struct.pack('i', Ch['FightDate'])
		Data += struct.pack('B', Ch['FightTicket'])
		Data += struct.pack('i', Ch['LeftSpecTime'])
		Data += struct.pack('i', Ch['WarCon'])
		Data += struct.pack('10s', Ch['LockMapName'])
		Data += struct.pack('i', Ch['LockMapTime'])
		Data += struct.pack('B', Ch['CruJob'])
		Data += struct.pack('i', Ch['CruConstructPoint'])
		Data += struct.pack('i', Ch['CruID'])
		Data += struct.pack('i', Ch['LeftDeadPenaltyTime'])
		Data += struct.pack('i', Ch['PartyID'])
		Data += struct.pack('h', Ch['GizonItemUpgradeLeft'])

		Data += struct.pack('B', len(OK['Item']))
		
		for each in OK['Item']:
			Data += struct.pack('20s', each['ItemName'])
			Data += struct.pack('i', each['Count'])
			Data += struct.pack('h', each['ItemType'])
			Data += struct.pack('i', each['ID1'])
			Data += struct.pack('i', each['ID2'])
			Data += struct.pack('i', each['ID3'])
			Data += struct.pack('B', each['Color'])
			Data += struct.pack('h', each['Effect1'])
			Data += struct.pack('h', each['Effect2'])
			Data += struct.pack('h', each['Effect3'])
			Data += struct.pack('h', each['LifeSpan'])
			Data += struct.pack('i', each['Attribute'])
			#Data += struct.pack('b', each['ItemEquip'])
			Data += chr(each['ItemEquip'] & 255)
			Data += struct.pack('h', each['ItemPosX'])
			Data += struct.pack('h', each['ItemPosY'])
			Data += struct.pack('i', each['ItemID'])

		Data += struct.pack('B', int("0")) #spacer

		Data += struct.pack('B', len(OK['Bank']))		
		for each in OK['Bank']:
			Data += struct.pack('20s', each['ItemName'])
			Data += struct.pack('i', each['Count'])
			Data += struct.pack('h', each['ItemType'])
			Data += struct.pack('i', each['ID1'])
			Data += struct.pack('i', each['ID2'])
			Data += struct.pack('i', each['ID3'])
			Data += struct.pack('B', each['Color'])
			Data += struct.pack('h', each['Effect1'])
			Data += struct.pack('h', each['Effect2'])
			Data += struct.pack('h', each['Effect3'])
			Data += struct.pack('h', each['LifeSpan'])
			Data += struct.pack('i', each['Attribute'])
			Data += struct.pack('i', each['ItemID'])

		Data += struct.pack('10s', Ch['Profile'])
		
		test = open("CHARDATA.dat", "w")
		try:
			test.write(Data)
		finally:
			test.close()
			
		print "DONE"
		#NEXT Packet -> (!) Gate Server -> Packet MsgID: MSGID_ENTERGAMECONFIRM (0x12A01006) 82b * '\x14\x0fAdmin\x00\x00\x0
		#		0\x00\x0086f7e437faa5a7fce15d1ddcb9eaeaea377667b8TOH\x00\x00\x00\x00\x00\x00\x00192.168.1.6\x00\x00\
		#		x00\x00\x00\x01\x00\x00\x00'(!) Gate Server -> Packet MsgID: MSGID_SERVERSTOCKMSG (0x3AE90013) 14b *
		#		 '\x14\x0f\x0etest\x00\x00\x00\x00\x00\x00\x00'
		return Data
	def ServerStockMsgHandler(self, GS, buffer):
		buffer = buffer[2:]
		global packet_format
		print "(*****) SERVERSTOCKMSGHANDLER : %s" % repr(buffer)
		while len(buffer)>0:
			ID = ord(buffer[0])
			buffer = buffer[1:]
			if ID == Packets.GSM_DISCONNECT:
				s=map(packet_format, struct.unpack('<10s', buffer[:10]))
				buffer=buffer[10:]
				Packet = namedtuple('Packet', 'PlayerName')._make(s)
				print "(***) GSM_DISCONNECT -> %s" % Packet.PlayerName
			elif ID == Packets.GSM_REQUEST_FINDCHARACTER:
				SendBuffer = buffer[:25]
				buffer = buffer[25:]
				InternalID = ord(SendBuffer[-1])
				print "(***) GSM_REQUEST_FINDCHARACTER InternalID=%d" % (InternalID)
				SendData=struct.pack('<Lh25s', MSGID_SERVERSTOCKMSG, DEF_MSGTYPE_CONFIRM, buffer)
				ok = False
				for i in self.GameServer.keys():
					if i == InternalID:
						self.SendMsgToGS(self.GameServer[i], SendData)
						ok = True
						
				if not ok:
					print "NOT OK."
				
			else:
				print "%04X" % ID

	def SavePlayerData(self, buffer, GS):
		global packet_format
		fmt = "<h10s10s10s"
		s=map(packet_format, struct.unpack(fmt, buffer[:struct.calcsize(fmt)]))
		Header = namedtuple("Header", "MsgType CharName AccountName AccountPassword")._make(s)
		buffer = buffer[struct.calcsize(fmt)+1:]
		Data = self.DecodeSavePlayerDataContents(buffer)
		if self.Database.SavePlayerContents(Header.CharName, Header.AccountName, Header.AccountPassword, Data):
			print "(!) Player [ %s ] data contents saved !"
		else:
			print "(!!!) Player [ %s ] data contents not saved !"

	def DecodeSavePlayerDataContents(self, buffer):
		global packet_format
		Values = "wYear wMonth wDay wHour wMinute wSecond m_cLocation m_cMapName " + \
					"m_sX m_sY m_cGuildName m_iGuildGuid m_cGuildRank " + \
					"m_iHP m_iMP m_iSP m_iLevel m_iRating m_iStr m_iVit " + \
					"m_iDex m_iInt m_iMag m_iAgi m_iLuck m_iExp m_iEnemyKillCount " + \
					"m_iPKCount m_iRewardGold m_iDownSkillIndex m_sCharIDnum1 " + \
					"m_sCharIDnum2 m_sCharIDnum3 m_cSex m_cSkin m_cHairStyle m_cHairColor " + \
					"m_cUnderwear m_iHungerStatus m_iTimeLeft_ShutUp m_iTimeLeft_Rating " + \
					"m_iTimeLeft_ForceRecall m_iTimeLeft_FirmStaminar m_iAdminUserLevel m_iBlockDate " + \
					"m_iQuest m_iQuestID m_iCurQuestCount m_iQuestRewardType m_iQuestRewardAmount " + \
					"m_iContribution m_iWarContribution m_bIsQuestCompleted m_iSpecialEventID " + \
					"m_iSuperAttackLeft m_iFightzoneNumber m_iReserveTime m_iFightZoneTicketNumber " + \
					"m_iSpecialAbilityTime m_cLockedMapName m_iLockedMapTime " + \
					"m_iCrusadeDuty m_dwCrusadeGUID m_iConstructionPoint m_iDeadPenaltyTime " + \
					"m_iPartyID m_iGizonItemUpgradeLeft m_iSpecialAbilityTime2 " + \
					"m_sAppr1 m_sAppr2 m_sAppr3 m_sAppr4 m_iApprColor MagicMastery"
		Values = Values.split(" ")
		format = "<hBBBBB10s10shh" # Y M D H M S LOC MAPNAME SX SY
		format += "20shhiii" #guildname guildrank guildguid hp mp sp
		format += "hiBBBBBB" #ilevel irating [stats * 6]
		format += "Biiiib" # m_iLuck m_iExp m_iEnemyKillCount m_iPKCount m_iRewardGold m_iDownSkillIndex
		format += "iii" #id1 id2 id3
		format += "BBBBBB" # sex skin hairstyl haircol underwear hunger
		format += "iiii" # shutup leftrating forcerecall firmstaminar
		format += "B20s" #adminlevel blockdate
		format += "hhhhi" #quests
		format += "iiBi" # m_iContribution m_iWarContribution m_bIsQuestCompleted m_iSpecialEventID 
		format += "hBiB" # m_iSuperAttackLeft m_iFightzoneNumber m_iReserveTime m_iFightZoneTicketNumber
		format += "i10si" #m_iSpecialAbilityTime m_cLockedMapName m_iLockedMapTime
		format += "Bii" #DUTY m_iCrusadeGUID m_iConstructionPoint
		format += "iih" #m_iDeadPenaltyTime m_iPartyID m_iGizonItemUpgradeLeft m_iSpecialAbilityTime2
		format += "iiiiii"  #m_sAppr1 m_sAppr2 m_sAppr3 m_sAppr4 m_iApprColor
		format += "100s" #Mastry

		SkillsFormat = "24B24I"
		ContentSize = struct.calcsize(format)
		SkillsSize = struct.calcsize(SkillsFormat)

		p = map(packet_format, struct.unpack(format, buffer[:ContentSize]))#Decode player contents + add profile
		Content = namedtuple('pp', " ".join(Values))._make(p) #make named structure
		Skills = struct.unpack(SkillsFormat,buffer[ContentSize:ContentSize + SkillsSize]) #skills [24*Skill%, 24*SkillSSN]
		Index = ContentSize + SkillsSize + 4
		NItems = ord(buffer[Index])
		Items = []
		if NItems > 0:
			for I in range(NItems):
				IndexForItem = (471 + (I*60))
				fmt = "<20sihiiiBhhhhiBhhI"
				Item = map(packet_format, struct.unpack(fmt, buffer[IndexForItem:IndexForItem + struct.calcsize(fmt)]))
				Item = namedtuple('Item', "m_cName m_dwCount m_sTouchEffectType m_sTouchEffectValue1 m_sTouchEffectValue2 m_sTouchEffectValue3 m_cItemColor m_sItemSpecEffectValue1 m_sItemSpecEffectValue2 m_sItemSpecEffectValue3 m_wCurLifeSpan m_dwAttribute m_bIsItemEquipped X Y ItemUniqueID")._make(Item)
				Items += [Item]
				
		Index = 471+(NItems*60)
		NBankItems = ord(buffer[Index])
		BankItems = []
		if NBankItems > 0:
			for I in range(NBankItems):
				IndexForItem = (Index+1+(I*55))
				fmt = "<20sihiiibhhhhii"
				Item = map(packet_format, struct.unpack(fmt, buffer[IndexForItem:IndexForItem + 55]))
				Item = namedtuple('Item', 'm_cName m_dwCount m_sTouchEffectType m_sTouchEffectValue1 m_sTouchEffectValue2 m_sTouchEffectValue3 m_cItemColor m_sItemSpecEffectValue1 m_sItemSpecEffectValue2 m_sItemSpecEffectValue3 m_wCurLifeSpan m_dwAttribute ItemUniqueID')._make(Item)
				BankItems += [Item]
				
		Index += (NBankItems*55)+1
		return {'Player': Content, 'Items': Items, 'BankItems': BankItems, 'Skills': Skills, 'Profile': buffer[Index:]}