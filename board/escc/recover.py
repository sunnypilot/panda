#!/usr/bin/env python3
import os
import time
import subprocess
import shutil

from panda import Panda, PandaDFU

board_path = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
  subprocess.check_call(f"scons -C {board_path}/../.. -j$(nproc) {board_path} --escc", shell=True)

  # --- HACK: SCons outputs our localized ESCC builds to 'board/escc/obj/'.
  # However, the upstream Panda Python library (PandaDFU / p.flash) hardcodes
  # its search path to the root 'board/obj/' directory. We copy the compiled 
  # binaries there so the hardware auto-picker can find them without us 
  # needing to modify and cause merge conflicts in the upstream library. ---
  os.makedirs(f"{board_path}/../obj", exist_ok=True)
  for f in os.listdir(f"{board_path}/obj"):
      shutil.copy(os.path.join(f"{board_path}/obj", f), f"{board_path}/../obj")

  for s in Panda.list():
    with Panda(serial=s) as p:
      print(f"putting {p.get_usb_serial()} in DFU mode")
      p.reset(enter_bootstub=True)
      p.reset(enter_bootloader=True)

  time.sleep(1)

  dfu_serials = PandaDFU.list()
  print(f"found {len(dfu_serials)} panda(s) in DFU - {dfu_serials}")
  for s in dfu_serials:
    print("flashing", s)
    PandaDFU(s).recover()
  exit(1 if len(dfu_serials) == 0 else 0)