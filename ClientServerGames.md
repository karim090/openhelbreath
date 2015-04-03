# Introduction #

Helbreath is one of many MMORPG, but is unique in it's gameplay, display and 2d techniques used. When you want to host this game, you need to know more about the structure of this type of games. Helbreath can run smootly because it is an client - server based game. The meaning of this will be discussed in this post.

# The big advantage of Client Server games. #

The best example of an Client-Server game is the all known, World of Warcraft. This runs smootly with high graphics etc. on most pc's. The cause of this is that many computations happen on the client's computer itself, the servers of World of Warcraft do need to compute that much for you.

In browser-based games, all computations are server sided, your computer is not loaded with computations to run a game. This is why Client - Server games have far more potential, graphics wise.

Helbreath is also an Client - Server based game, this means, one of the disadvantages, you have to download files. In the case of HB this is about 300 mb, where WoW has 3.1 gb on files to download and even more. So HB is a more lightweight in it's class.

# An example of communication #

  1. You and your group approach an Abbadon (High lvl monster). All of your clients send information to the server about where you are. The server knows where the Abbadon is if you get too close, you'll pull him by accident, at which point he'll probably kill your party.
  1. Once you're in range, someone in your party attacks the Abbadon. That person's client informs the server of the attack. The server responds by causing the Abbadon to attack your party and to verbally taunt you. It relays this information to your computers.
  1. As you're fighting, your party's clients tell the server which spells you're casting. Based on your character's statistics, the server calculates your damage and healing. It relays that information to your clients, so each player can see what's happening to all the others. Other players' clients are doing the same thing, so you can see how they fare during the battle as well.
  1. When you successfully kill the Abbadon, the server instructs your clients to play its death animation (located on your own pc). If not, the server instructs the Abbadon to further taunt each killed player.
  1. When the Abbadon dies, the server consults its loot table and lets each client know which items dropped. The clients display these items on each player's screen. The players decide who will receive the items.
  1. When a player collects an item, the client removes the image of the item from the screen and places an icon representing it in the player's inventory. The client also tells the server that the player has done so, and the server instructs the other clients to remove that item from their game view.

In PvP this is a little bit different, the calculation of damage are still done on the server but other players control the enemy on the sreen.

Source: http://electronics.howstuffworks.com/world-of-warcraft6.htm