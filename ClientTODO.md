# Introduction #

For developers - please work on items with higher priority first. High priority often means important functionality.

# Details #

This list will be constantly updated. These tasks are left till the Milestone 1 release. _Remember, priorities may change_.

<font color='red'><b>Critical</b></font> > <font color='darkred'><b>High</b></font> > <font color='orange'><b>Medium</b></font> > <font color='darkgreen'><b>Low</b></font> > <font color='silver'><b>Very low</b></font>

# Updates #
  * ## 19.04.2010 ##
> > First version

# The list #

| **Name** | **Priority** | **Description** | **Done in rev.** | **Author** | Finished |
|:---------|:-------------|:----------------|:-----------------|:-----------|:---------|
| Draw Objects | <font color='red'><b>Critical</b></font> | Universal and efficient way to draw objects such as NPC or Players. _Refeer to `DrawObject_*` in original sources_ | _N/A_ | _N/A_ | _N/A_ |
| Network code | <font color='red'><b>Critical</b></font> | Connecting to Game Server, download data and keep the connection alive. | _N/A_ | _N/A_ |  _N/A_ |
| Map loader | <font color='darkred'><b>High</b></font> | Map handling. This data should be cached. Data loading only on map change (_depends on **DEF`_`CACHE**_) | _N/A_ | _N/A_ | _N/A_ |
| Logging in | <font color='darkred'><b>High</b></font> | Authorization using login and password | <a href='http://code.google.com/p/openhelbreath/source/detail?r=102'><a href='https://code.google.com/p/openhelbreath/source/detail?r=102'>revision 102</a></a> | Drajwer | **Yes** |
| Game scene | <font color='darkred'><b>High</b></font> | Interface, HP, MP, SP bars. GUI. Basic support on drawing players and objects. | _N/A_ | _N/A_ | _N/A_ |
| Sprite fonts | <font color='orange'><b>Medium</b></font> | Loading and drawing sprite fonts onto surfaces. | <a href='http://code.google.com/p/openhelbreath/source/detail?r=98'><a href='https://code.google.com/p/openhelbreath/source/detail?r=98'>revision 98</a></a> | todevorek | **Mostly** |
| Map display | <font color='orange'><b>Medium</b></font> | Efficient drawing and scrolling map. | _N/A_ | _N/A_ | _N/A_ |
| New account | <font color='darkgreen'><b>Low</b></font> | Account signup from SignupScene.cpp. _This functionality no longer exists in original clients such as HBUsa._ | <a href='http://code.google.com/p/openhelbreath/source/detail?r=129'><a href='https://code.google.com/p/openhelbreath/source/detail?r=129'>revision 129</a></a> | Drajwer | **Yes** |
| Account manage | <font color='darkgreen'><b>Low</b></font> | Create new character, change password, delete character. | _N/A_ | _N/A_ | _N/A_ |
| Mobile support | <font color='silver'><b>Very low</b></font> | At least one try to compile with mobile toolchains (PSPDev, Symbian?) before Milestone 1. (?) | _N/A_ | _N/A_ | _N/A_ |