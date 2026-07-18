import ctypes

#C dynamic linked library, needing to generate a .so file , gcc -fPIC -shared -o clibrary.so clib.c
clibrary = ctypes.CDLL("/home/hootsoon/AVC/avcMVNT/UCA_homeR/py-c/clibrary.so")
clibrary.helloWorld()