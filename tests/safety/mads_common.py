import unittest
from abc import abstractmethod


class MadsCommonBase(unittest.TestCase):
    @abstractmethod
    def _lkas_button_msg(self, enabled):
        raise NotImplementedError

    @abstractmethod
    def _acc_state_msg(self, enabled):
        raise NotImplementedError

    # def test_enable_control_from_main(self):
    #     for enable_mads in (True, False):
    #         with self.subTest("enable_mads", mads_enabled=enable_mads):
    #             self.safety.set_enable_mads(enable_mads, False)
    #             for acc_state_msg_valid in (True, False):
    #                 with self.subTest("acc_state_msg", state_valid=acc_state_msg_valid):
    #                     msg = self._acc_state_msg(acc_state_msg_valid)
    #                     self._rx(msg)
    #                     self.assertEqual(acc_state_msg_valid, self.safety.get_acc_main_on(), f"msg: {hex(msg.addr)}")

    # def test_lkas_button(self):
    #     for enable_mads in (True, False):
    #         with self.subTest("enable_mads", enable_mads=enable_mads):
    #             self.safety.set_enable_mads(enable_mads)
    #             self.safety.set_controls_allowed_lat(False)
    #             self._rx(self._lkas_button_msg(enable_mads))
    #             self.assertEqual(enable_mads, self.safety.get_is_lat_active())
