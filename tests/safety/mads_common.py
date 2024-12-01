import unittest
from abc import abstractmethod


class MadsCommonBase(unittest.TestCase):
    @abstractmethod
    def _lkas_button_msg(self, enabled):
        raise NotImplementedError

    @abstractmethod
    def _acc_state_msg(self, enabled):
        raise NotImplementedError

    def test_enable_control_from_main_button_prev(self):
        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                for main_button_prev in (-1, 0, 1):
                    with self.subTest("main_button_prev", button_state=main_button_prev):
                        self.safety.set_main_button_prev(main_button_prev)
                        self._rx(self._user_brake_msg(False))
                        self.assertEqual(enable_mads and main_button_prev == 1, self.safety.get_controls_allowed_lat(),
                                         (f"main_button_prev: [{self.safety.get_main_button_prev()}] | " +
                                          f"mads_state_flags: [{self.safety.get_mads_state_flags()}: {bin(self.safety.get_mads_state_flags())}] | " +
                                          f"main_transition: [{self.safety.get_mads_main_button_transition()}], " +
                                          f"cur [{self.safety.get_mads_main_button_current()}], " +
                                          f"last [{self.safety.get_mads_main_button_last()}]"))

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
