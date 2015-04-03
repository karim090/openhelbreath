# Introduction #

In the wiki page about ClientServerGames there was more information about a basic set up and communication within a Client Server game like Helbreath. This page will contain more information about the old, common used Helbreath architecture. Most of the time it is quite a mess with understanding the servers etc. I hope to paint a more clear picture here.

Note: this is about the architecture not used in openhelbreath but used in the standard helbreath servers.

# A picture paints it.. #

![http://img704.imageshack.us/img704/623/oldgameserverstructurel.png](http://img704.imageshack.us/img704/623/oldgameserverstructurel.png)

**note: another node could be the "Client Files" node, this is linked to the Client node and these are the files that are on the player's computer.**

# Details about the architecture (that are not shown) #

Compared to the new architecture made here, there are more nodes in this graph.
First we have the player, you, when playing Helbreath.
Then there is the package, the information send between the client and the server.
This information goes directly to the GateServer and the MainLogServer.
The red circled lines represent services that the hoster has to start to get the Server running.

All the GameServers could also be linked together because they communicate with each other. This is vital for sending messages between maps. This is for later documentation.

# MainLogSever #

The MainLogServer connects to the WorldLogServer and asks the data on a player.
It handles the registration and the player login.
The MainLogServer also sends GameServer adresses and ports together with an character list when the player is succesfully logged in.

# World Log Server #

The WorldLogServer is mainly a database. It can save player data and retrieves it. This data will be communicated with the MainLogServer. In the old game architecture, the data is stored in .txt files, the new one uses MySQL.

# GateServer #

The GateServer handles registration from the MainLogServer to the GameServers. But the most important function of this server is that it communicates between the GameServers. It can send messages from one GameServer to another or sends it to the Client through sending a package.

# GameServer #
In the GameServers the maps are running. Every GameServer can communicate with each other, and communicates player information to the GateServer.
An example is that it communicates player locations in maps to the GateServer. Note that one GameServer does not nessecarily hosts all the maps. Most of the time this is spread over more GameServer so that if one GamServer crashes other maps stay online.

# Terminology #

The GameServer is often reffered as the HG Server, the Helbreath GameServer.