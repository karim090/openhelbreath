# Introduction #

This script works on all platforms.  If you have a database already, it is recommended you backup your database before you run this script.

# Details #

  1. Have python installed
  1. Edit these values in ASCII-to-SQL.py.  Tell the script the correct directories, and give the correct SQL authentication information.
    * **host** should point to SQL server IP.
    * **port** should point to SQL server Port.
    * **user** and **passwd** should be the user and password to login to SQL server.
```
# Config
cAccountDir	= "C:\\Account\\Account"        # Current ASCII Account directory
cCharacterDir	= "C:\\Account\\Character"      # Current ASCII Character directory
MySQL_Auth = {'host' : '192.168.1.50', 'port': 3306, 'user': 'test', 'passwd': 'test', 'db': 'playerdb'}
```
  1. Run the script and follow the directions.  You should see something like this:
```
C:\Users\H2>python C:\Users\H2\Desktop\sHelbreath\Tools\ASCII-to-SQL.py
OpenHelbreath ASCII-to-SQL Convertion Tool (Version: 1.00)
Copyright (C) 2009 by Hypnotoad
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it under certain conditions.

(*) 3 Account found - 1 Character found
(*) Connecting to MySQL database...
(*) Connection to MySQL database was successfully established!

ASCII-to-SQL Convertion Tool will add all files to the database.
Characters without an account will not be added and become orphaned.
The ASCII *.txt files will not be deleted and must be removed manually.

Are you sure you want to continue? (Y/N):y
(*) Begin converting account files...
(*) ...Done!

(*) Begin converting character files...
(*) ...Done!

Finished : Success!

----------
Statistics
----------

Account
  3/3 Accounts converted

Character
  1/1 Characters converted

Character/Bank Item
  7/7 Items Added

Admin (Account:Character)
['rune2:CrazyAdmin']

(*) For more detailed information check ConvertLog.txt
(*) SQL dump saved to ASCII-Import-10-11-2009-200101.sql

Press ENTER to QUIT
```