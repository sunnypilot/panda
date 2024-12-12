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
    self.safety.set_mads_button_press(-1)
    self.safety.set_controls_allowed_lat(False)
    self.safety.set_controls_requested_lat(False)
    self.safety.set_acc_main_on(False)
    self.safety.set_mads_params(False, False, False)

  def test_enable_and_disable_control_allowed_with_mads_button(self):
    """Toggle MADS with MADS button"""
    try:
      self._lkas_button_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because MADS button is not supported")

    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", mads_enabled=enable_mads):
          for acc_main_on in (True, False):
            with self.subTest("acc_main_on", acc_main_on=acc_main_on):
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, False, False)
              self.safety.set_acc_main_on(acc_main_on)

              self._rx(self._lkas_button_msg(True))
              self._rx(self._lkas_button_msg(False))
              self.assertEqual(enable_mads and acc_main_on, self.safety.get_controls_allowed_lat())

              self._rx(self._lkas_button_msg(True))
              self._rx(self._lkas_button_msg(False))
              self.assertFalse(self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_enable_control_allowed_with_manual_acc_main_on_state(self):
    try:
      self._acc_state_msg(False)
    except NotImplementedError:
      self._mads_states_cleanup()
      raise unittest.SkipTest("Skipping test because _acc_state_msg is not implemented for this car")

    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", mads_enabled=enable_mads):
          for main_cruise_allowed in (True, False):
            with self.subTest("main_cruise_allowed", button_state=main_cruise_allowed):
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, False, main_cruise_allowed)
              self._rx(self._acc_state_msg(main_cruise_allowed))
              self._rx(self._speed_msg(0))
              self.assertEqual(enable_mads and main_cruise_allowed, self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_enable_control_allowed_with_manual_mads_button_state(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", mads_enabled=enable_mads):
          for mads_button_press in (-1, 0, 1):
            with self.subTest("mads_button_press", button_state=mads_button_press):
              for acc_main_on in (True, False):
                with self.subTest("acc_main_on", acc_main_on=acc_main_on):
                  self._mads_states_cleanup()
                  self.safety.set_mads_params(enable_mads, False, False)
                  self.safety.set_acc_main_on(acc_main_on)

                  self.safety.set_mads_button_press(mads_button_press)
                  self._rx(self._speed_msg(0))
                  self.assertEqual(enable_mads and acc_main_on and mads_button_press == 1, self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_enable_control_allowed_from_acc_main_on(self):
    """Test that lateral controls are allowed when ACC main is enabled and disabled when ACC main is disabled"""
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", mads_enabled=enable_mads):
          for acc_main_on in (True, False):
            with self.subTest("initial_acc_main", initial_acc_main=acc_main_on):
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, False, True)

              # Set initial state
              self.safety.set_acc_main_on(acc_main_on)
              self._rx(self._speed_msg(0))
              expected_lat = enable_mads and acc_main_on
              self.assertEqual(expected_lat, self.safety.get_controls_allowed_lat(),
                               f"Expected lat: [{expected_lat}] when acc_main_on goes to [{acc_main_on}]")

              # Test transition to opposite state
              self.safety.set_acc_main_on(not acc_main_on)
              self._rx(self._speed_msg(0))
              expected_lat = enable_mads and not acc_main_on
              self.assertEqual(expected_lat, self.safety.get_controls_allowed_lat(),
                               f"Expected lat: [{expected_lat}] when acc_main_on goes from [{acc_main_on}] to [{not acc_main_on}]")

              # Test transition back to initial state
              self.safety.set_acc_main_on(acc_main_on)
              self._rx(self._speed_msg(0))
              expected_lat = enable_mads and acc_main_on
              self.assertEqual(expected_lat, self.safety.get_controls_allowed_lat(),
                               f"Expected lat: [{expected_lat}] when acc_main_on goes from [{not acc_main_on}] to [{acc_main_on}]")
    finally:
      self._mads_states_cleanup()

  def test_controls_requested_lat_from_acc_main_on(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", mads_enabled=enable_mads):
          self._mads_states_cleanup()
          self.safety.set_mads_params(enable_mads, False, True)

          self.safety.set_acc_main_on(True)
          self._rx(self._speed_msg(0))
          self.assertEqual(enable_mads, self.safety.get_controls_requested_lat())

          self.safety.set_acc_main_on(False)
          self._rx(self._speed_msg(0))
          self.assertFalse(self.safety.get_controls_requested_lat())
    finally:
      self._mads_states_cleanup()

  def test_disengage_lateral_on_brake_setup(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          for disengage_on_brake in (True, False):
            with self.subTest("disengage on brake", disengage_on_brake=disengage_on_brake):
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, disengage_on_brake, False)
              self.assertEqual(enable_mads and disengage_on_brake, self.safety.get_disengage_lateral_on_brake())
    finally:
      self._mads_states_cleanup()

  def test_disengage_lateral_on_brake(self):
    try:
      self._mads_states_cleanup()
      self.safety.set_mads_params(True, True, False)

      self._rx(self._user_brake_msg(False))
      self.safety.set_controls_requested_lat(True)
      self.safety.set_controls_allowed_lat(True)

      self._rx(self._user_brake_msg(True))
      # Test we pause lateral
      self.assertFalse(self.safety.get_controls_allowed_lat())
      # Make sure we can re-gain lateral actuation
      self._rx(self._user_brake_msg(False))
      self.assertTrue(self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_no_disengage_lateral_on_brake(self):
    try:
      self._mads_states_cleanup()
      self.safety.set_mads_params(True, False, False)

      self._rx(self._user_brake_msg(False))
      self.safety.set_controls_requested_lat(True)
      self.safety.set_controls_allowed_lat(True)

      self._rx(self._user_brake_msg(True))
      self.assertTrue(self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_allow_engage_with_brake_pressed(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          for disengage_lateral_on_brake in (True, False):
            with self.subTest("disengage_lateral_on_brake", disengage_lateral_on_brake=disengage_lateral_on_brake):
              for main_cruise_allowed in (True, False):
                with self.subTest("main_cruise_allowed", main_cruise_allowed=main_cruise_allowed):
                  self._mads_states_cleanup()
                  self.safety.set_mads_params(enable_mads, disengage_lateral_on_brake, main_cruise_allowed)

                  self._rx(self._user_brake_msg(True))
                  self.safety.set_controls_requested_lat(True)
                  self._rx(self._user_brake_msg(True))
                  self.assertEqual(enable_mads, self.safety.get_controls_allowed_lat())
                  self._rx(self._user_brake_msg(True))
                  self.assertEqual(enable_mads, self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_mads_button_press_with_acc_main_on(self):
    """Test that MADS button presses disengage controls when main cruise is on"""
    try:
      self._lkas_button_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because MADS button is not supported")

    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          self._mads_states_cleanup()
          self.safety.set_mads_params(enable_mads, False, True)
          self.safety.set_acc_main_on(True)
          self.assertFalse(self.safety.get_controls_allowed_lat())

          # Enable controls initially with MADS button
          self._rx(self._lkas_button_msg(True))
          self._rx(self._lkas_button_msg(False))
          self._rx(self._speed_msg(0))
          self.assertEqual(enable_mads, self.safety.get_controls_allowed_lat())

          # Test MADS button press while ACC main is on
          self._rx(self._lkas_button_msg(True))
          self._rx(self._lkas_button_msg(False))
          self._rx(self._speed_msg(0))

          # Controls should be disabled
          self.assertFalse(self.safety.get_controls_allowed_lat(),
                          "Controls should be disabled with MADS button press while ACC main is on")
    finally:
      self._mads_states_cleanup()

  def test_enable_lateral_control_with_controls_allowed_rising_edge(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          self._mads_states_cleanup()
          self.safety.set_mads_params(enable_mads, False, False)

          self.safety.set_controls_allowed(False)
          self._rx(self._speed_msg(0))
          self.safety.set_controls_allowed(True)
          self._rx(self._speed_msg(0))
          self.assertTrue(self.safety.get_controls_allowed())
          self.assertEqual(enable_mads, self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_controls_allowed_must_always_enable_lateral_control(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          for controls_allowed in (True, False):
            with self.subTest("controls allowed", controls_allowed=controls_allowed):
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, False, False)
              self.safety.set_controls_allowed(False)
              self._rx(self._speed_msg(0))

              self.safety.set_controls_allowed(controls_allowed)
              self._rx(self._speed_msg(0))
              expected_lat = enable_mads and self.safety.get_controls_allowed()
              self.assertEqual(expected_lat, self.safety.get_controls_allowed_lat())
    finally:
      self.safety.set_controls_allowed(False)
      self._rx(self._speed_msg(0))
      self._mads_states_cleanup()

  def test_alternative_experience_always_allow_mads_button(self):
    try:
      self._lkas_button_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because MADS button is not supported")

    try:
      self._mads_states_cleanup()
      self.safety.set_mads_params(True, False, False)

      self._rx(self._lkas_button_msg(True))
      self._rx(self._lkas_button_msg(False))
      self._rx(self._speed_msg(0))
      self.assertTrue(self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_alternative_experience_flag_setting(self):
    """Test setting of alternative experience flags"""
    try:
      self._mads_states_cleanup()

      # Test main_cruise_allowed behavior
      # 1. Set all bits EXCEPT main_cruise_allowed
      self.safety.set_mads_params(True, False, False)
      self.assertFalse(self.safety.get_main_cruise_allowed(),
                       "main_cruise_allowed should be false when its bit is not set")

      # 2. Set ONLY main_cruise_allowed
      self.safety.set_mads_params(True, False, True)
      self.assertTrue(self.safety.get_main_cruise_allowed(),
                      "main_cruise_allowed should be true when its bit is set")

      # Test zero handling
      # 1. No bits set
      self.safety.set_mads_params(False, False, False)
      self.assertFalse(self.safety.get_main_cruise_allowed(),
                       "main_cruise_allowed should be false when no bits are set")

      # 2. Only MADS enabled with target bits false
      self.safety.set_mads_params(True, False, False)
      self.assertFalse(self.safety.get_main_cruise_allowed(),
                       "main_cruise_allowed should be false when only MADS is enabled")

      # Test all combinations for always_allow_mads_button (to catch != vs == mutation)
      test_combinations = [
        (True, False, False),  # MADS only
        (True, False, True),   # MADS + cruise
        (True, False, True),     # all enabled
      ]

      for params in test_combinations:
        self.safety.set_mads_params(*params)
        self.assertEqual(params[2], self.safety.get_main_cruise_allowed(),
                         f"main_cruise_allowed mismatch for params {params}")

    finally:
      self._mads_states_cleanup()

  def test_enable_control_allowed_with_mads_button_and_disable_with_main_cruise(self):
    """Tests main cruise and MADS button state transitions.

      Sequence:
      1. Main cruise off -> on
      2. MADS button disengage
      3. MADS button engage
      4. Main cruise off

    """
    try:
      self._lkas_button_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because MADS button is not supported")

    try:
      self._acc_state_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because _acc_state_msg is not implemented for this car")

    try:
      self._mads_states_cleanup()
      self.safety.set_mads_params(True, False, True)

      self._rx(self._acc_state_msg(True))
      self._rx(self._speed_msg(0))
      self.assertTrue(self.safety.get_controls_allowed_lat())

      self._rx(self._lkas_button_msg(True))
      self._rx(self._lkas_button_msg(False))
      self.assertFalse(self.safety.get_controls_allowed_lat())

      self._rx(self._lkas_button_msg(True))
      self._rx(self._lkas_button_msg(False))
      self.assertTrue(self.safety.get_controls_allowed_lat())

      self._rx(self._acc_state_msg(False))
      self._rx(self._speed_msg(0))
      self.assertFalse(self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_mads_button_combinations(self):
    """Test various MADS engagement/disengagement button combinations.
    Tests different combinations of main cruise and MADS buttons for lateral control.

    Scenarios:
    1. Main cruise toggle only
    2. Main cruise then MADS button
    3. MADS button then main cruise
    4. MADS button toggle only
    """
    scenarios = [
      ("main_cruise_toggle", "cruise", True, "cruise", False),
      ("main_cruise_then_mads_button", "cruise", True, "lkas", False),
      ("mads_button_then_main_cruise", "lkas", True, "cruise", True),
      ("mads_button_toggle", "lkas", True, "lkas", False),
    ]

    try:
      self._lkas_button_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because MADS button is not supported")

    try:
      self._acc_state_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because _acc_state_msg is not implemented for this car")

    for name, first_button, first_expected, second_button, second_expected in scenarios:
      with self.subTest(msg=name):
        try:
          self._mads_states_cleanup()
          self.safety.set_mads_params(True, False, True)

          # First action
          if first_button == "cruise":
            self._rx(self._acc_state_msg(True))
          else:  # MADS button
            self._rx(self._lkas_button_msg(True))
            self._rx(self._lkas_button_msg(False))

          self._rx(self._speed_msg(0))
          self.assertEqual(first_expected, self.safety.get_controls_allowed_lat(),
                           f"{name}: Expected lat control {first_expected} after first action")

          # Second action
          if second_button == "cruise":
            self._rx(self._acc_state_msg(False))
          else:  # MADS button
            self._rx(self._lkas_button_msg(True))
            self._rx(self._lkas_button_msg(False))

          self._rx(self._speed_msg(0))
          self.assertEqual(second_expected, self.safety.get_controls_allowed_lat(),
                           f"{name}: Expected lat control {second_expected} after second action")

        finally:
          self._mads_states_cleanup()
