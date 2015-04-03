# Introduction #

This works on all platforms. We recommend that you should run this server under dedicated Linux hosting and run Game Servers on other machines.

See [project progress](Progress.md) for details.
# Details #

  1. Download Python 2.6.x. **NOT 3.x** and Install
  1. Download MySQLdb package for Python 2.6. MySQLdb does not support 2.6 python yet. You can find this here: http://sourceforge.net/projects/mysql-python/
  1. Download LoginServer, and unpack .py files to **/your\_directory**
  1. Create file LServer.cfg in /your\_directory and write:
```
login-server-address     = Your external IP address 
login-server-port        = Main Login port (2848)
gate-server-port     	 = Gate Server port (6502)

max-total-users          = Max total users allowed to connect
world-server-name        = Name of world server (30 char max)

permitted-address        = 127.0.0.1
```
  1. If not exists, create dir /your\_directory/Config and /your\_directory/Logs
  1. Copy your config files to /your\_directory/Config
  1. Install MySQL software
  1. If needed edit Database.py and following lines:
```
MySQL_Auth = {'host' : 'localhost', 'port': 3306, 'user': 'root', 'passwd': '', 'db': 'playerdb'}
```
> Server will check database integration at startup.

Now you have everything done. Run from /your\_directory.
```
cd /your_directory
python main.py
```

You should see this:

```
OpenHelbreath Login Server 0.0.0.1
Copyright (C) 2009 by Drajwer
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it under certain conditions.
(*) Login server address : 127.0.0.1
(*) Login server port : 2848
(*) Gate Server port : 6502
(*) Max total users allowed on server : 0
(*) World Server Name : WS1
(*) IP [127.0.0.1] added to permitted addresses list!
(*) Connecting to MySQL database...
(*) Connection to MySQL database was sucessfully established!
(*) Reading configuration file [Config/Item.cfg] -> {'Item'}...
(*) Reading configuration file [Config/Item2.cfg] -> {'Item2'}...
(*) Reading configuration file [Config/Item3.cfg] -> {'Item3'}...
(*) Reading configuration file [Config/BuildItem.cfg] -> {'BuildItem'}...
(*) Reading configuration file [Config/DupItemID.cfg] -> {'DupItemID'}...
(*) Reading configuration file [Config/Magic.cfg] -> {'Magic'}...
(*) Reading configuration file [Config/noticement.txt] -> {'noticement'}...
(*) Reading configuration file [Config/NPC.cfg] -> {'NPC'}...
(*) Reading configuration file [Config/Potion.cfg] -> {'Potion'}...
(*) Reading configuration file [Config/Quest.cfg] -> {'Quest'}...
(*) Reading configuration file [Config/Skill.cfg] -> {'Skill'}...
(*) Reading configuration file [Config/AdminSettings.cfg] -> {'AdminSettings'}...
(*) Reading configuration file [Config/Settings.cfg] -> {'Settings'}...
(*) Done!
(*) Gate server successfully started!
(*) GateServer -> Server open
(*) Login server sucessfully started!
(*) MainSocket -> Server open
```

---

Permitted address gate server will accept only. Any other GS registration will be rejected and reported. **We recommend to set up these lines, if not server will listen to all addresses and this could lead to "[Extasis hack](ExtasisHack.md)" vulnerable.**