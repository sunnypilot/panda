import unittest
from abc import abstractmethod
from enum import IntFlag


class MadsStates(IntFlag):
  DEFAULT = 0
  RESERVED = 1
  MAIN_BUTTON_AVAILABLE = 2
  LKAS_BUTTON_AVAILABLE = 4


class MadsCommonBase(unittest.TestCase):
  @abstractmethod
  def _lkas_button_msg(self, enabled):
    raise NotImplementedError

  @abstractmethod
  def _main_cruise_button_msg(self, enabled):
    try:
      self._button_msg(enabled)
    except (NotImplementedError, AttributeError):
      raise unittest.SkipTest("Skipping test because _button_msg is not implemented for this car. If you know it, please implement it.")

    raise NotImplementedError("Since _button_msg is implemented, _main_cruise_button_msg should be implemented as well to signal the main cruise button press")

  @abstractmethod
  def _acc_state_msg(self, enabled):
    raise NotImplementedError

  def test_enable_control_from_cruise_button_press(self):
    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        for cruise_button_press in [True, False]:
          self.safety.set_enable_mads(enable_mads, False)
          with self.subTest("cruise_button_press", cruise_button_press=cruise_button_press):
            self._mads_states_cleanup()
            self._rx(self._main_cruise_button_msg(cruise_button_press))
            self.assertEqual(enable_mads and cruise_button_press, self.safety.get_controls_allowed_lat())
    self._mads_states_cleanup()

  def test_enable_control_from_lkas_button_press(self):
    try:
      self._lkas_button_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because _lkas_button_msg is not implemented for this car")

    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        for lkas_button_press in [True, False]:
          self.safety.set_enable_mads(enable_mads, False)
          with self.subTest("lkas_button_press", button_state=lkas_button_press):
            self._mads_states_cleanup()
            self._rx(self._lkas_button_msg(lkas_button_press))
            self.assertEqual(enable_mads and lkas_button_press, self.safety.get_controls_allowed_lat())
    self._mads_states_cleanup()

  def _mads_states_cleanup(self):
    self.safety.set_main_button_press(-1)
    self.safety.set_lkas_button_press(-1)
    self.safety.set_controls_allowed_lat(False)
    self.safety.set_main_button_engaged(False)
    self.safety.set_lkas_button_engaged(False)
    self.safety.set_mads_state_flags(0)
    self.safety.set_acc_main_on(False)

  def test_enable_control_from_setting_main_state_manually(self):
    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        self.safety.set_enable_mads(enable_mads, False)
        for main_button_press in (-1, 0, 1):
          with self.subTest("main_button_press", button_state=main_button_press):
            self._mads_states_cleanup()
            self.safety.set_main_button_press(main_button_press)
            self._rx(self._speed_msg(0))
            self.assertEqual(enable_mads and main_button_press == 1, self.safety.get_controls_allowed_lat())
    self._mads_states_cleanup()

  def test_enable_control_from_setting_lkas_state_manually(self):
    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        self.safety.set_enable_mads(enable_mads, False)
        for lkas_button_press in (-1, 0, 1):
          with self.subTest("lkas_button_press", button_state=lkas_button_press):
            self._mads_states_cleanup()
            self.safety.set_lkas_button_press(lkas_button_press)
            self._rx(self._speed_msg(0))
            self.assertEqual(enable_mads and lkas_button_press == 1, self.safety.get_controls_allowed_lat())
    self._mads_states_cleanup()

  def test_mads_state_flags(self):
    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        self.safety.set_enable_mads(enable_mads, False)
        self._mads_states_cleanup()
        self.safety.set_main_button_press(0)  # Meaning a message with those buttons was seen and the _prev inside is no longer -1
        self.safety.set_lkas_button_press(0)  # Meaning a message with those buttons was seen and the _prev inside is no longer -1
        self._rx(self._speed_msg(0))
        self.assertTrue(self.safety.get_mads_state_flags() & MadsStates.MAIN_BUTTON_AVAILABLE)
        self.assertTrue(self.safety.get_mads_state_flags() & MadsStates.LKAS_BUTTON_AVAILABLE)
    self._mads_states_cleanup()

  def test_enable_control_from_acc_main_on(self):
    """Test that lateral controls are allowed when ACC main is enabled"""
    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        self.safety.set_enable_mads(enable_mads, False)
        for acc_main_on in (True, False):
          with self.subTest("acc_main_on", acc_main_on=acc_main_on):
            self._mads_states_cleanup()
            self.safety.set_acc_main_on(acc_main_on)
            self._rx(self._speed_msg(0))
            self.assertEqual(enable_mads and acc_main_on, self.safety.get_controls_allowed_lat())
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
    Specifically targets the mutation of & to | in flag checking operations.
    Tests both setting and clearing of flags to catch potential bitwise operation mutations."""

    # Test both MADS enabled and disabled states
    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        self.safety.set_enable_mads(enable_mads, False)
        self._mads_states_cleanup()

        # Initial state - both flags should be unset
        self._rx(self._speed_msg(0))
        initial_flags = self.safety.get_mads_state_flags()
        self.assertEqual(initial_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.DEFAULT)  # Main button flag
        self.assertEqual(initial_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.DEFAULT)  # LKAS button flag

        # Set only main button
        self.safety.set_main_button_press(0)
        self._rx(self._speed_msg(0))
        main_only_flags = self.safety.get_mads_state_flags()
        self.assertEqual(main_only_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.MAIN_BUTTON_AVAILABLE)  # Main button flag should be set
        self.assertEqual(main_only_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.DEFAULT)  # LKAS button flag should still be unset

        # Set LKAS button and verify both flags
        self.safety.set_lkas_button_press(0)
        self._rx(self._speed_msg(0))
        both_flags = self.safety.get_mads_state_flags()
        self.assertEqual(both_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.MAIN_BUTTON_AVAILABLE)  # Main button flag should remain set
        self.assertEqual(both_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.LKAS_BUTTON_AVAILABLE)  # LKAS button flag should be set

        # Verify that using | instead of & would give different results
        self.assertNotEqual(both_flags & MadsStates.MAIN_BUTTON_AVAILABLE, both_flags | MadsStates.MAIN_BUTTON_AVAILABLE)
        self.assertNotEqual(both_flags & MadsStates.LKAS_BUTTON_AVAILABLE, both_flags | MadsStates.LKAS_BUTTON_AVAILABLE)

        # Reset flags and verify they're cleared
        self._mads_states_cleanup()
        self._rx(self._speed_msg(0))
        cleared_flags = self.safety.get_mads_state_flags()
        self.assertEqual(cleared_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.DEFAULT)
        self.assertEqual(cleared_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.DEFAULT)

  def test_mads_state_flags_persistence(self):
    """Test to verify that state flags remain set once buttons are seen"""

    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        self.safety.set_enable_mads(enable_mads, False)
        self._mads_states_cleanup()

        # Set main button and verify flag
        self.safety.set_main_button_press(0)
        self._rx(self._speed_msg(0))
        self.assertEqual(self.safety.get_mads_state_flags() & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.MAIN_BUTTON_AVAILABLE)

        # Reset main button to -1, flag should persist
        self.safety.set_main_button_press(-1)
        self._rx(self._speed_msg(0))
        self.assertEqual(self.safety.get_mads_state_flags() & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.MAIN_BUTTON_AVAILABLE)

        # Set LKAS button and verify both flags
        self.safety.set_lkas_button_press(0)
        self._rx(self._speed_msg(0))
        flags = self.safety.get_mads_state_flags()
        self.assertEqual(flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.MAIN_BUTTON_AVAILABLE)
        self.assertEqual(flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.LKAS_BUTTON_AVAILABLE)

  def test_mads_state_flags_individual_control(self):
    """Test the ability to individually control state flags.
    Verifies that flags can be set and cleared independently."""

    for enable_mads in (True, False):
      with self.subTest("enable_mads", mads_enabled=enable_mads):
        self.safety.set_enable_mads(enable_mads, False)
        self._mads_states_cleanup()

        # Set main button flag only
        self.safety.set_main_button_press(0)
        self._rx(self._speed_msg(0))
        main_flags = self.safety.get_mads_state_flags()
        self.assertEqual(main_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.MAIN_BUTTON_AVAILABLE)
        self.assertEqual(main_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.DEFAULT)

        # Reset flags and set LKAS only
        self._mads_states_cleanup()
        self.safety.set_lkas_button_press(0)
        self._rx(self._speed_msg(0))
        lkas_flags = self.safety.get_mads_state_flags()
        self.assertEqual(lkas_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.DEFAULT)
        self.assertEqual(lkas_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.LKAS_BUTTON_AVAILABLE)

        # Set both flags
        self._mads_states_cleanup()
        self.safety.set_main_button_press(0)
        self.safety.set_lkas_button_press(0)
        self._rx(self._speed_msg(0))
        both_flags = self.safety.get_mads_state_flags()
        self.assertEqual(both_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.MAIN_BUTTON_AVAILABLE)
        self.assertEqual(both_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.LKAS_BUTTON_AVAILABLE)

        # Clear all flags and verify
        self._mads_states_cleanup()
        self._rx(self._speed_msg(0))
        final_flags = self.safety.get_mads_state_flags()
        self.assertEqual(final_flags & MadsStates.MAIN_BUTTON_AVAILABLE, MadsStates.DEFAULT)
        self.assertEqual(final_flags & MadsStates.LKAS_BUTTON_AVAILABLE, MadsStates.DEFAULT)
