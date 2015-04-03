# Introduction #

As Game Server code is platform independent, I will describe here how to setup IDE (Eclipse) for Windows and Linux.

### Eclipse under Windows ###

  1. Download Eclipse for Windows
  1. Setup g++, make, MinGW etc. This document will help you -> http://max.berger.name/howto/cdt/
  1. Configure PATH.
  1. Reboot

Try from terminal (open -> cmd.exe) if you can use compilers. If so, please skip to setting up Project workspace.

### Eclipse under Linux ###

  1. Download package for your distribution.

Thats it.

# Setting up Project workspace #

  1. Download latest source code.
  1. From Eclipse: New -> C++ Project -> Empty project. Under Windows you should see (and use) MinGW toolchain.
  1. Set project name to GameServer
  1. Set location to /path/svn/GameServer. You must have existing code in this folder.
  1. Finish

Eclipse is smart enough to set up everything for us. Also, it should build it automagically.

Hope this help. If not mail me drajwer@gmail.com or Wave me drajwer@googlewave.com