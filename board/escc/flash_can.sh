#!/usr/bin/env sh
set -e

cd ..
scons -u -j$(nproc) --escc
cd escc

../../tests/escc/enter_canloader.py obj/panda_h7.bin.signed