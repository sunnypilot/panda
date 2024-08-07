#!/usr/bin/env sh
set -e

cd ..
scons -u -j$(nproc)
cd escc

../../tests/escc/enter_canloader.py obj/escc.bin.signed
