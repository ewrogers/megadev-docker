#!/bin/sh
set -eu
python3 /build/fetch-sources.py gcc binutils
mkdir -p /build/gcc /build/binutils /build/gcc-build /build/binutils-build
tar -xf /opt/sources/gcc.tar.xz --strip-components=1 -C /build/gcc
tar -xf /opt/sources/binutils.tar.xz --strip-components=1 -C /build/binutils
cd /build/binutils-build
/build/binutils/configure --target=m68k-elf --prefix=/opt/m68k \
    --disable-nls --disable-werror --with-system-zlib
make -j"${BUILD_JOBS:-4}"
make install
export PATH=/opt/m68k/bin:$PATH
cd /build/gcc-build
/build/gcc/configure --target=m68k-elf --prefix=/opt/m68k \
    --with-cpu=m68000 --enable-languages=c --without-headers --disable-threads \
    --disable-nls --disable-shared --disable-multilib --disable-libssp \
    --disable-libgomp --disable-libquadmath --disable-libsanitizer \
    --with-system-zlib
make -j"${BUILD_JOBS:-4}" all-gcc all-target-libgcc
make install-gcc install-target-libgcc
rm -rf /build/gcc /build/binutils /build/gcc-build /build/binutils-build
