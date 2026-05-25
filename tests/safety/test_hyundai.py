#!/usr/bin/env python3
import random
import re
import unittest
from pathlib import Path
from panda import Panda
from panda.tests.libpanda import libpanda_py
import panda.tests.safety.common as common
from panda.tests.safety.common import CANPackerPanda
from panda.tests.safety.hyundai_common import HyundaiButtonBase, HyundaiLongitudinalBase


# 4 bit checkusm used in some hyundai messages
# lives outside the can packer because we never send this msg
def checksum(msg):
  addr, dat, bus = msg

  chksum = 0
  if addr == 0x386:
    for i, b in enumerate(dat):
      for j in range(8):
        # exclude checksum and counter bits
        if (i != 1 or j < 6) and (i != 3 or j < 6) and (i != 5 or j < 6) and (i != 7 or j < 6):
          bit = (b >> j) & 1
        else:
          bit = 0
        chksum += bit
    chksum = (chksum ^ 9) & 0xF
    ret = bytearray(dat)
    ret[5] |= (chksum & 0x3) << 6
    ret[7] |= (chksum & 0xc) << 4
  else:
    for i, b in enumerate(dat):
      if addr in [0x260, 0x421] and i == 7:
        b &= 0x0F if addr == 0x421 else 0xF0
      elif addr == 0x394 and i == 6:
        b &= 0xF0
      elif addr == 0x394 and i == 7:
        continue
      chksum += sum(divmod(b, 16))
    chksum = (16 - chksum) % 16
    ret = bytearray(dat)
    ret[6 if addr == 0x394 else 7] |= chksum << (4 if addr == 0x421 else 0)

  return addr, ret, bus


class TestHyundaiSafety(HyundaiButtonBase, common.PandaCarSafetyTest, common.DriverTorqueSteeringSafetyTest, common.SteerRequestCutSafetyTest):
  TX_MSGS = [[0x340, 0], [0x4F1, 0], [0x485, 0]]
  STANDSTILL_THRESHOLD = 12  # 0.375 kph
  RELAY_MALFUNCTION_ADDRS = {0: (0x340,)}  # LKAS11
  FWD_BLACKLISTED_ADDRS = {2: [0x340, 0x485]}
  FWD_BUS_LOOKUP = {0: 2, 2: 0}

  MAX_RATE_UP = 3
  MAX_RATE_DOWN = 7
  MAX_TORQUE = 384
  MAX_RT_DELTA = 112
  RT_INTERVAL = 250000
  DRIVER_TORQUE_ALLOWANCE = 50
  DRIVER_TORQUE_FACTOR = 2

  # Safety around steering req bit
  MIN_VALID_STEERING_FRAMES = 89
  MAX_INVALID_STEERING_FRAMES = 2
  MIN_VALID_STEERING_RT_INTERVAL = 810000  # a ~10% buffer, can send steer up to 110Hz

  cnt_gas = 0
  cnt_speed = 0
  cnt_brake = 0
  cnt_cruise = 0
  cnt_button = 0

  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI, 0)
    self.safety.init_tests()

  def _button_msg(self, buttons, main_button=0, bus=0):
    values = {"CF_Clu_CruiseSwState": buttons, "CF_Clu_CruiseSwMain": main_button, "CF_Clu_AliveCnt1": self.cnt_button}
    self.__class__.cnt_button += 1
    return self.packer.make_can_msg_panda("CLU11", bus, values)

  def _user_gas_msg(self, gas):
    values = {"CF_Ems_AclAct": gas, "AliveCounter": self.cnt_gas % 4}
    self.__class__.cnt_gas += 1
    return self.packer.make_can_msg_panda("EMS16", 0, values, fix_checksum=checksum)

  def _user_brake_msg(self, brake):
    values = {"DriverOverride": 2 if brake else random.choice((0, 1, 3)),
              "AliveCounterTCS": self.cnt_brake % 8}
    self.__class__.cnt_brake += 1
    return self.packer.make_can_msg_panda("TCS13", 0, values, fix_checksum=checksum)

  def _speed_msg(self, speed):
    # panda safety doesn't scale, so undo the scaling
    values = {"WHL_SPD_%s" % s: speed * 0.03125 for s in ["FL", "FR", "RL", "RR"]}
    values["WHL_SPD_AliveCounter_LSB"] = (self.cnt_speed % 16) & 0x3
    values["WHL_SPD_AliveCounter_MSB"] = (self.cnt_speed % 16) >> 2
    self.__class__.cnt_speed += 1
    return self.packer.make_can_msg_panda("WHL_SPD11", 0, values, fix_checksum=checksum)

  def _pcm_status_msg(self, enable):
    values = {"ACCMode": enable, "CR_VSM_Alive": self.cnt_cruise % 16}
    self.__class__.cnt_cruise += 1
    return self.packer.make_can_msg_panda("SCC12", self.SCC_BUS, values, fix_checksum=checksum)

  def _torque_driver_msg(self, torque):
    values = {"CR_Mdps_StrColTq": torque}
    return self.packer.make_can_msg_panda("MDPS12", 0, values)

  def _torque_cmd_msg(self, torque, steer_req=1):
    values = {"CR_Lkas_StrToqReq": torque, "CF_Lkas_ActToi": steer_req}
    return self.packer.make_can_msg_panda("LKAS11", 0, values)

  def _acc_state_msg(self, enable):
    values = {"MainMode_ACC": enable, "AliveCounterACC": self.cnt_cruise % 16}
    self.__class__.cnt_cruise += 1
    return self.packer.make_can_msg_panda("SCC11", self.SCC_BUS, values)

  def _lkas_button_msg(self, enabled):
    values = {"LFA_Pressed": enabled}
    return self.packer.make_can_msg_panda("BCM_PO_11", 0, values)

  def _main_cruise_button_msg(self, enabled):
    return self._button_msg(0, enabled)

  def test_pcm_main_cruise_state_availability(self):
    """Test that ACC main state is correctly set when receiving 0x420 message, toggling HYUNDAI_LONG flag"""
    prior_safety_mode = self.safety.get_current_safety_mode()
    prior_safety_param = self.safety.get_current_safety_param()

    for hyundai_longitudinal in (True, False):
      with self.subTest("hyundai_longitudinal", hyundai_longitudinal=hyundai_longitudinal):
        self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI, 0 if hyundai_longitudinal else Panda.FLAG_HYUNDAI_LONG)
        for should_turn_acc_main_on in (True, False):
          with self.subTest("acc_main_on", should_turn_acc_main_on=should_turn_acc_main_on):
            self._rx(self._acc_state_msg(should_turn_acc_main_on))  # Send the ACC state message
            expected_acc_main = should_turn_acc_main_on and hyundai_longitudinal  # ACC main should only be set if hyundai_longitudinal is True
            self.assertEqual(expected_acc_main, self.safety.get_acc_main_on())
    self.safety.set_safety_hooks(prior_safety_mode, prior_safety_param)


class TestHyundaiSafetyAltLimits(TestHyundaiSafety):
  MAX_RATE_UP = 2
  MAX_RATE_DOWN = 3
  MAX_TORQUE = 270

  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI, Panda.FLAG_HYUNDAI_ALT_LIMITS)
    self.safety.init_tests()


class TestHyundaiSafetyCameraSCC(TestHyundaiSafety):
  BUTTONS_TX_BUS = 2  # tx on 2, rx on 0
  SCC_BUS = 2  # rx on 2

  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI, Panda.FLAG_HYUNDAI_CAMERA_SCC)
    self.safety.init_tests()

  def test_pcm_main_cruise_state_availability(self):
    """
    Test that ACC main state is correctly set when receiving 0x420 message.
    For camera SCC, ACC main should always be on when receiving 0x420 message
    """

    for should_turn_acc_main_on in (True, False):
      with self.subTest("acc_main_on", should_turn_acc_main_on=should_turn_acc_main_on):
        self._rx(self._acc_state_msg(should_turn_acc_main_on))
        self.assertEqual(should_turn_acc_main_on, self.safety.get_acc_main_on())


class TestHyundaiLegacySafety(TestHyundaiSafety):
  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI_LEGACY, 0)
    self.safety.init_tests()


class TestHyundaiLegacySafetyEV(TestHyundaiSafety):
  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI_LEGACY, 1)
    self.safety.init_tests()

  def _user_gas_msg(self, gas):
    values = {"Accel_Pedal_Pos": gas}
    return self.packer.make_can_msg_panda("E_EMS11", 0, values, fix_checksum=checksum)


class TestHyundaiLegacySafetyHEV(TestHyundaiSafety):
  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI_LEGACY, 2)
    self.safety.init_tests()

  def _user_gas_msg(self, gas):
    values = {"CR_Vcu_AccPedDep_Pos": gas}
    return self.packer.make_can_msg_panda("E_EMS11", 0, values, fix_checksum=checksum)

class TestHyundaiLongitudinalSafety(HyundaiLongitudinalBase, TestHyundaiSafety):
  TX_MSGS = [[0x340, 0], [0x4F1, 0], [0x485, 0], [0x420, 0], [0x421, 0], [0x50A, 0], [0x389, 0], [0x4A2, 0], [0x38D, 0], [0x483, 0], [0x7D0, 0]]

  RELAY_MALFUNCTION_ADDRS = {0: (0x340, 0x421)}  # LKAS11, SCC12

  DISABLED_ECU_UDS_MSG = (0x7D0, 0)
  DISABLED_ECU_ACTUATION_MSG = (0x421, 0)

  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI, Panda.FLAG_HYUNDAI_LONG)
    self.safety.init_tests()

  def _accel_msg(self, accel, aeb_req=False, aeb_decel=0):
    values = {
      "aReqRaw": accel,
      "aReqValue": accel,
      "AEB_CmdAct": int(aeb_req),
      "CR_VSM_DecCmd": aeb_decel,
    }
    return self.packer.make_can_msg_panda("SCC12", self.SCC_BUS, values)

  def _fca11_msg(self, idx=0, vsm_aeb_req=False, fca_aeb_req=False, aeb_decel=0):
    values = {
      "CR_FCA_Alive": idx % 0xF,
      "FCA_Status": 2,
      "CR_VSM_DecCmd": aeb_decel,
      "CF_VSM_DecCmdAct": int(vsm_aeb_req),
      "FCA_CmdAct": int(fca_aeb_req),
    }
    return self.packer.make_can_msg_panda("FCA11", 0, values)

  def _tx_acc_state_msg(self, enable):
    values = {"MainMode_ACC": enable}
    return self.packer.make_can_msg_panda("SCC11", 0, values)

  def test_no_aeb_fca11(self):
    self.assertTrue(self._tx(self._fca11_msg()))
    self.assertFalse(self._tx(self._fca11_msg(vsm_aeb_req=True)))
    self.assertFalse(self._tx(self._fca11_msg(fca_aeb_req=True)))
    self.assertFalse(self._tx(self._fca11_msg(aeb_decel=1.0)))

  def test_no_aeb_scc12(self):
    self.assertTrue(self._tx(self._accel_msg(0)))
    self.assertFalse(self._tx(self._accel_msg(0, aeb_req=True)))
    self.assertFalse(self._tx(self._accel_msg(0, aeb_decel=1.0)))


class TestHyundaiLongitudinalESCCSafety(HyundaiLongitudinalBase, TestHyundaiSafety):
  TX_MSGS = [[0x340, 0], [0x4F1, 0], [0x485, 0], [0x420, 0], [0x421, 0], [0x50A, 0], [0x389, 0]]

  RELAY_MALFUNCTION_ADDRS = {0: (0x340, 0x421)}  # LKAS11, SCC12

  def setUp(self):
    self.packer = CANPackerPanda("hyundai_kia_generic")
    self.safety = libpanda_py.libpanda
    self.safety.set_safety_hooks(Panda.SAFETY_HYUNDAI, Panda.FLAG_HYUNDAI_LONG | Panda.FLAG_HYUNDAI_ESCC)
    self.safety.init_tests()

  def _accel_msg(self, accel, aeb_req=False, aeb_decel=0):
    values = {
      "aReqRaw": accel,
      "aReqValue": accel,
    }
    return self.packer.make_can_msg_panda("SCC12", self.SCC_BUS, values)

  def _tx_acc_state_msg(self, enable):
    values = {"MainMode_ACC": enable}
    return self.packer.make_can_msg_panda("SCC11", 0, values)

  def test_tester_present_allowed(self):
    pass

  def test_disabled_ecu_alive(self):
    pass


class TestHyundaiESCCFwdSafety(common.PandaSafetyTestBase):
  # Keep in sync with board/safety.h.
  SAFETY_HYUNDAI_ESCC = 29
  TX_MSGS = []
  RADAR_TX_QUEUE_MIN_SLOTS = 50
  NON_SCC_ADDR = 0x123
  SCC_ADDRS = (0x420, 0x421, 0x50A, 0x389)

  def setUp(self):
    self.safety = libpanda_py.libpanda
    safety_h = Path(__file__).parents[2] / "board" / "safety.h"
    match = re.search(r"#define\s+SAFETY_HYUNDAI_ESCC\s+(\d+)U", safety_h.read_text())
    self.assertIsNotNone(match)
    self.assertEqual(self.SAFETY_HYUNDAI_ESCC, int(match.group(1)))
    if self.safety.set_safety_hooks(self.SAFETY_HYUNDAI_ESCC, 0) != 0:
      raise unittest.SkipTest("SAFETY_HYUNDAI_ESCC is not compiled into libpanda")
    self.safety.init_tests()
    self._clear_radar_tx_queue()

  def _clear_radar_tx_queue(self):
    msg = libpanda_py.ffi.new('CANPacket_t *')
    while self.safety.can_pop(self.safety.tx3_q, msg):
      pass

  def _fill_radar_tx_queue_to_empty_slots(self, empty_slots):
    msg = common.make_msg(2, self.NON_SCC_ADDR, 8)
    while self.safety.can_slots_empty(self.safety.tx3_q) > empty_slots:
      self.assertTrue(self.safety.can_push(self.safety.tx3_q, msg))

  def test_car_to_radar_forwards_when_radar_queue_has_space(self):
    self.assertGreaterEqual(self.safety.can_slots_empty(self.safety.tx3_q), self.RADAR_TX_QUEUE_MIN_SLOTS)
    self.assertEqual(2, self.safety.safety_fwd_hook(0, self.NON_SCC_ADDR))

  def test_car_to_radar_drops_when_radar_queue_below_threshold(self):
    self._fill_radar_tx_queue_to_empty_slots(self.RADAR_TX_QUEUE_MIN_SLOTS - 1)

    self.assertEqual(self.RADAR_TX_QUEUE_MIN_SLOTS - 1, self.safety.can_slots_empty(self.safety.tx3_q))
    self.assertEqual(-1, self.safety.safety_fwd_hook(0, self.NON_SCC_ADDR))

  def test_car_to_radar_threshold_boundary(self):
    self._fill_radar_tx_queue_to_empty_slots(self.RADAR_TX_QUEUE_MIN_SLOTS)
    self.assertEqual(self.RADAR_TX_QUEUE_MIN_SLOTS, self.safety.can_slots_empty(self.safety.tx3_q))
    self.assertEqual(2, self.safety.safety_fwd_hook(0, self.NON_SCC_ADDR))

    self.assertTrue(self.safety.can_push(self.safety.tx3_q, common.make_msg(2, self.NON_SCC_ADDR, 8)))
    self.assertEqual(self.RADAR_TX_QUEUE_MIN_SLOTS - 1, self.safety.can_slots_empty(self.safety.tx3_q))
    self.assertEqual(-1, self.safety.safety_fwd_hook(0, self.NON_SCC_ADDR))

  def test_radar_to_car_forwards_when_radar_queue_below_threshold(self):
    self._fill_radar_tx_queue_to_empty_slots(self.RADAR_TX_QUEUE_MIN_SLOTS - 1)

    self.assertEqual(0, self.safety.safety_fwd_hook(2, self.NON_SCC_ADDR))

  def test_bus_one_is_not_forwarded(self):
    self.assertEqual(-1, self.safety.safety_fwd_hook(1, self.NON_SCC_ADDR))

  def test_sunnypilot_scc_block_preserved(self):
    self.safety.set_timer(1000)
    self.assertEqual(-1, self.safety.safety_fwd_hook(0, 0x420))

    for addr in self.SCC_ADDRS:
      with self.subTest(addr=addr):
        self.assertEqual(-1, self.safety.safety_fwd_hook(2, addr))

  def test_sunnypilot_scc_block_expires(self):
    self.safety.set_timer(1000)
    self.safety.safety_fwd_hook(0, 0x420)

    self.safety.set_timer(151001)

    self.assertEqual(0, self.safety.safety_fwd_hook(2, 0x420))


if __name__ == "__main__":
  unittest.main()
