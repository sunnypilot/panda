import unittest
from abc import abstractmethod


class MadsCommonBase(unittest.TestCase):
    @abstractmethod
    def _lkas_button_msg(self, enabled):
        raise NotImplementedError

    @abstractmethod
    def _acc_state_msg(self, enabled):
        raise NotImplementedError

    def _mads_states_cleanup(self):
        self.safety.set_main_button_prev(-1)
        self.safety.set_lkas_button_prev(-1)
        self.safety.set_controls_allowed_lat(False)
        self.safety.set_main_button_engaged(False)
        self.safety.set_lkas_button_engaged(False)

    def test_enable_control_from_main_button_prev(self):
        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                for main_button_prev in (-1, 0, 1):
                    with self.subTest("main_button_prev", button_state=main_button_prev):
                        self._mads_states_cleanup()
                        self.safety.set_main_button_prev(main_button_prev)
                        self._rx(self._user_brake_msg(False))
                        self.assertEqual(enable_mads and main_button_prev == 1, self.safety.get_controls_allowed_lat())
        self._mads_states_cleanup()

    def test_enable_control_from_lkas_button_prev(self):
        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                for lkas_button_prev in (-1, 0, 1):
                    with self.subTest("lkas_button_prev", button_state=lkas_button_prev):
                        self._mads_states_cleanup()
                        self.safety.set_lkas_button_prev(lkas_button_prev)
                        self._rx(self._user_brake_msg(False))
                        self.assertEqual(enable_mads and lkas_button_prev == 1, self.safety.get_controls_allowed_lat())
        self._mads_states_cleanup()

    def test_mads_state_flags(self):
        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                self._mads_states_cleanup()
                self.safety.set_main_button_prev(0)  # Meaning a message with those buttons was seen and the _prev inside is no longer -1
                self.safety.set_lkas_button_prev(0)  # Meaning a message with those buttons was seen and the _prev inside is no longer -1
                self._rx(self._user_brake_msg(False))
                self.assertTrue(self.safety.get_mads_state_flags() & 2)
                self.assertTrue(self.safety.get_mads_state_flags() & 4)
        self._mads_states_cleanup()

    def test_controls_allowed_must_always_enable_lat(self):
        for mads_enabled in [True, False]:
            with self.subTest("mads enabled", mads_enabled=mads_enabled):
                self.safety.set_enable_mads(mads_enabled, False)
                for controls_allowed in [True, False]:
                    with self.subTest("controls allowed", controls_allowed=controls_allowed):
                        self.safety.set_controls_allowed(controls_allowed)
                        self.assertEqual(self.safety.get_controls_allowed(), self.safety.get_lat_active())

    def test_mads_disengage_lat_on_brake_setup(self):
        for mads_enabled in [True, False]:
            with self.subTest("mads enabled", mads_enabled=mads_enabled):
                for disengage_on_brake in [True, False]:
                    with self.subTest("disengage on brake", disengage_on_brake=disengage_on_brake):
                        self.safety.set_enable_mads(mads_enabled, disengage_on_brake)
                        self.assertEqual(disengage_on_brake, self.safety.get_disengage_lat_on_brake())

    def test_mads_state_flags_mutation(self):
        """Test to catch mutations in bitwise operations for state flags.
        Specifically targets the mutation of & to | in flag checking operations."""

        # Test both MADS enabled and disabled states
        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                self._mads_states_cleanup()

                # Initial state - both flags should be unset
                self._rx(self._user_brake_msg(False))
                initial_flags = self.safety.get_mads_state_flags()
                self.assertEqual(initial_flags & 2, 0)  # Main button flag
                self.assertEqual(initial_flags & 4, 0)  # LKAS button flag

                # Set only main button
                self.safety.set_main_button_prev(0)
                self._rx(self._user_brake_msg(False))
                main_only_flags = self.safety.get_mads_state_flags()
                self.assertEqual(main_only_flags & 2, 2)  # Main button flag should be set
                self.assertEqual(main_only_flags & 4, 0)  # LKAS button flag should still be unset

                # Add LKAS button
                self.safety.set_lkas_button_prev(0)
                self._rx(self._user_brake_msg(False))
                both_flags = self.safety.get_mads_state_flags()
                self.assertEqual(both_flags & 2, 2)  # Main button flag should remain set
                self.assertEqual(both_flags & 4, 4)  # LKAS button flag should be set

                # Verify that using | instead of & would give different results
                # This helps catch the mutation
                self.assertNotEqual(both_flags & 2, both_flags | 2)
                self.assertNotEqual(both_flags & 4, both_flags | 4)

                # Reset buttons to -1, but flags should remain set
                self._mads_states_cleanup()
                self._rx(self._user_brake_msg(False))
                final_flags = self.safety.get_mads_state_flags()
                self.assertEqual(final_flags & 2, 2)  # Main button flag should still be set
                self.assertEqual(final_flags & 4, 4)  # LKAS button flag should still be set

    def test_mads_state_flags_persistence(self):
        """Test to verify that state flags remain set once buttons are seen"""

        for enable_mads in (True, False):
            with self.subTest("enable_mads", mads_enabled=enable_mads):
                self.safety.set_enable_mads(enable_mads, False)
                self._mads_states_cleanup()

                # Set main button and verify flag
                self.safety.set_main_button_prev(0)
                self._rx(self._user_brake_msg(False))
                self.assertEqual(self.safety.get_mads_state_flags() & 2, 2)

                # Reset main button to -1, flag should persist
                self.safety.set_main_button_prev(-1)
                self._rx(self._user_brake_msg(False))
                self.assertEqual(self.safety.get_mads_state_flags() & 2, 2)

                # Set LKAS button and verify both flags
                self.safety.set_lkas_button_prev(0)
                self._rx(self._user_brake_msg(False))
                flags = self.safety.get_mads_state_flags()
                self.assertEqual(flags & 2, 2)
                self.assertEqual(flags & 4, 4)

                # Reset both buttons to -1, flags should remain
                self._mads_states_cleanup()
                self._rx(self._user_brake_msg(False))
                final_flags = self.safety.get_mads_state_flags()
                self.assertEqual(final_flags & 2, 2)
                self.assertEqual(final_flags & 4, 4)
