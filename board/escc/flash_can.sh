#!/usr/bin/env sh
set -e

cd ..
scons -u -j$(nproc) --escc
cd escc

../../tests/escc/enter_canloader.py obj/escc.bin.signed
