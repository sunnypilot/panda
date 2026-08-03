from opendbc.car.structs import CarParams

from panda.tests.libpanda import libpanda_py


HYUNDAI_CANFD_LFA_CAMERA_SYNC_PARAM = 2 | 8 | 1024  # HYBRID_GAS | CAMERA_SCC | LFA_CAMERA_SYNC


def lfa_command(torque: int, mode: int, magic: int = 0xA5):
  dat = torque.to_bytes(2, byteorder="little", signed=True) + bytes([mode, magic, 0, 0, 0, 0])
  return libpanda_py.make_CANPacket(0x7FF, 0, dat)


def test_internal_lfa_command_is_consumed_without_can_tx():
  panda = libpanda_py.libpanda
  assert panda.set_safety_hooks(CarParams.SafetyModel.hyundaiCanfd, HYUNDAI_CANFD_LFA_CAMERA_SYNC_PARAM) == 0

  slots_before = panda.can_slots_empty(panda.tx1_q)
  blocked_before = panda.safety_tx_blocked
  panda.can_send(lfa_command(0, 1), 0, False)

  assert panda.can_slots_empty(panda.tx1_q) == slots_before
  assert panda.safety_tx_blocked == blocked_before


def test_invalid_internal_lfa_command_is_rejected_not_transmitted():
  panda = libpanda_py.libpanda
  assert panda.set_safety_hooks(CarParams.SafetyModel.hyundaiCanfd, HYUNDAI_CANFD_LFA_CAMERA_SYNC_PARAM) == 0

  slots_before = panda.can_slots_empty(panda.tx1_q)
  blocked_before = panda.safety_tx_blocked
  panda.can_send(lfa_command(0, 1, magic=0), 0, False)

  assert panda.can_slots_empty(panda.tx1_q) == slots_before
  assert panda.safety_tx_blocked == blocked_before + 1
