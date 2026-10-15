#!/bin/sh
set -eu
python3 /build/fetch-sources.py --lock /build/debugger.lock.json gdb
mkdir -p /build/gdb /build/gdb-build
tar -xf /opt/sources/gdb.tar.xz --strip-components=1 -C /build/gdb
cd /build/gdb-build
/build/gdb/configure --target=m68k-elf --prefix=/opt/m68k \
    --disable-nls --disable-sim --disable-werror --with-python=python3 \
    --with-system-zlib --enable-tui
make -j"${BUILD_JOBS:-4}" all-gdb
make install-gdb
rm -rf /build/gdb /build/gdb-build
