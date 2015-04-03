# Introduction #

openhelbreath is in many ways a project to make Open Source Helbreath better, this especially holds for the architecture which will be discussed in this page.
The biggest change in the new architecture is the coming of the LoginServer, this simplifies the model significantly.

# A picture paints it.. #

![http://img705.imageshack.us/img705/9008/newgameserverstructure.png](http://img705.imageshack.us/img705/9008/newgameserverstructure.png)

# Details about the architecture #

There is an LoginServer and an MySQL database added.

# LoginServer #

This is what makes openhelbreath unique, a LoginServer coded in Python that replaces the MainLogServer, the WorldLogServer and the GateServer. These three servers are now in one server and are totally reviewed in functioning.
When a player goes to another map, the LoginServer communicates to the GameServer if that map is available, next it will move the player to another GameServer.

# Database #

In the old Helbreath the data was stored in .txt files, now they are stored in a MySQL database. The LoginServer communicates this data to the database.

# Terminology #

The GameServer is often reffered as the HG Server, the Helbreath GameServer.