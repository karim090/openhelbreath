## Compiling Client on Windows ##
1. Install MSYS. Here you will find how to do it: http://www.mingw.org/wiki/MSYS

2. Install MinGW http://www.mingw.org/wiki/HOWTO_Install_the_MinGW_GCC_Compiler_Suite

3. Set MinGW path in msys\etc\fstab. It should look like this:
```
#Win32_Path		Mount_Point
c:/mingw		/mingw
```
4. Download
  * SDL-devel-1.2.14-mingw32.tar.gz from http://www.libsdl.org/download-1.2.php
  * SDL\_image-devel-1.2.10-VC.zip from http://www.libsdl.org/projects/SDL_image/
  * SDL\_mixer-devel-1.2.11-VC.zip from http://www.libsdl.org/projects/SDL_mixer/
  * SDL\_ttf-devel-2.0.9-VC8.zip from http://www.libsdl.org/projects/SDL_ttf/

5. Unpack archives and copy or move files from unpacked folders to MinGW location:
  * lib to c:\MinGW\lib
  * include (whole SDL catalog) to c:\MinGw\include
  * bin to c:\MinGW\bin

6. Edit prefix in c:\MinGW\bin\sdl-config
```
prefix=/mingw
```
7. Download client source from svn

8. Run msys and move to folder where you downloaded source. This is done by the command:
```
cd c:/<folder-name>
```
9. Do
```
./configure.sh
make
```