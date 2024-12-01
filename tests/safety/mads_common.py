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
                        self.safety.set_lkas_button_prev(-1) # Force to not have LKAS
                        self._rx(self._user_brake_msg(False))
                        self.assertEqual(enable_mads and main_button_prev == 1, self.safety.get_controls_allowed_lat())

    def test_enable_control_from_lkas_button_prev(self):
        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                for lkas_button_prev in (-1, 0, 1):
                    with self.subTest("lkas_button_prev", button_state=lkas_button_prev):
                        self.safety.set_main_button_prev(-1)
                        self.safety.set_lkas_button_prev(lkas_button_prev)
                        self._rx(self._user_brake_msg(False))
                        self.assertEqual(enable_mads and lkas_button_prev == 1, self.safety.get_controls_allowed_lat())

    def test_mads_state_flags(self):
        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                self.safety.set_main_button_prev(0)
                self.safety.set_lkas_button_prev(0)
                self._rx(self._user_brake_msg(False))
                self.assertTrue(self.safety.get_mads_state_flags() & 2)
                self.assertTrue(self.safety.get_mads_state_flags() & 4)
        self.safety.set_main_button_prev(-1)
        self.safety.set_lkas_button_prev(-1)