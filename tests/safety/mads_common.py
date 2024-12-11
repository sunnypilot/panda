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
    self.safety.set_mads_params(False, False, False, False, False)

  def test_enable_and_disable_control_allowed_with_mads_button(self):
    """Toggle MADS with MADS button"""
    try:
      self._lkas_button_msg(False)
    except NotImplementedError:
      raise unittest.SkipTest("Skipping test because MADS button is not supported")

    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", mads_enabled=enable_mads):
          self._mads_states_cleanup()
          self.safety.set_mads_params(enable_mads, False, False, False, False)

          self._rx(self._lkas_button_msg(True))
          self._rx(self._lkas_button_msg(False))
          self.assertEqual(enable_mads, self.safety.get_controls_allowed_lat())

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
              self.safety.set_mads_params(enable_mads, False, main_cruise_allowed, False, False)
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
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, False, False, False, False)
              self.safety.set_mads_button_press(mads_button_press)
              self._rx(self._speed_msg(0))
              self.assertEqual(enable_mads and mads_button_press == 1, self.safety.get_controls_allowed_lat())
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
              self.safety.set_mads_params(enable_mads, False, True, False, False)

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
          self.safety.set_mads_params(enable_mads, False, True, False, False)

          self.safety.set_acc_main_on(True)
          self._rx(self._speed_msg(0))
          self.assertEqual(enable_mads, self.safety.get_controls_requested_lat())

          self.safety.set_acc_main_on(False)
          self._rx(self._speed_msg(0))
          self.assertFalse(self.safety.get_controls_requested_lat())
    finally:
      self._mads_states_cleanup()

  def test_controls_allowed_must_always_enable_lateral_control(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          self.safety.set_mads_params(enable_mads, False, False, False, False)
          for controls_allowed in (True, False):
            with self.subTest("controls allowed", controls_allowed=controls_allowed):
              self.safety.set_controls_allowed(controls_allowed)
              self.assertEqual(self.safety.get_controls_allowed(), self.safety.get_lat_active())
    finally:
      self._mads_states_cleanup()

  def test_mads_disengage_lateral_on_brake_setup(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          for disengage_on_brake in (True, False):
            with self.subTest("disengage on brake", disengage_on_brake=disengage_on_brake):
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, disengage_on_brake, False, False, False)
              self.assertEqual(enable_mads and disengage_on_brake, self.safety.get_disengage_lateral_on_brake())
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
          self.safety.set_mads_params(enable_mads, False, True, False, False)
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
      self._mads_states_cleanup()
      raise unittest.SkipTest("Skipping test because _acc_state_msg is not implemented for this car")

    try:
      self._mads_states_cleanup()
      self.safety.set_mads_params(True, False, True, False, False)

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

  # Unified Engagement Mode tests
  def test_enable_lateral_control_with_controls_allowed_rising_edge(self):
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", enable_mads=enable_mads):
          for unified_engagement_mode in (True, False):
            with self.subTest("unified_engagement_mode", unified_engagement_mode=unified_engagement_mode):
              self._mads_states_cleanup()
              self.safety.set_mads_params(enable_mads, False, False, unified_engagement_mode, False)

              self.safety.set_controls_allowed(False)
              self._rx(self._speed_msg(0))
              self.safety.set_controls_allowed(True)
              self._rx(self._speed_msg(0))
              self.assertTrue(self.safety.get_controls_allowed())
              self.assertEqual(enable_mads and unified_engagement_mode, self.safety.get_controls_allowed_lat())
    finally:
      self._mads_states_cleanup()

  def test_enable_lateral_control_with_controls_allowed_transitions(self):
    """Test lateral control behavior with controls_allowed transitions in unified engagement mode"""
    try:
      for enable_mads in (True, False):
        with self.subTest("enable_mads", mads_enabled=enable_mads):
          for unified_engagement_mode in (True, False):
            with self.subTest("unified_engagement_mode", unified_engagement_mode=unified_engagement_mode):
              for controls_allowed in (True, False):
                with self.subTest("initial_controls_allowed", initial_controls=controls_allowed):
                  self._mads_states_cleanup()
                  # Ensure controls are off before enabling features
                  self.safety.set_controls_allowed(False)
                  self._rx(self._speed_msg(0))

                  # Now set up MADS parameters
                  self.safety.set_mads_params(enable_mads, False, False, unified_engagement_mode, False)
                  expected_lat = False

                  # Verify clean initial state
                  self.assertFalse(self.safety.get_controls_allowed_lat(),
                                   "Lateral control should be disabled in clean initial state")

                  # Set desired initial state
                  self.safety.set_controls_allowed(controls_allowed)
                  self._rx(self._speed_msg(0))
                  # Only enable on rising edge
                  if controls_allowed and unified_engagement_mode and enable_mads:
                    expected_lat = True
                  self.assertEqual(expected_lat, self.safety.get_controls_allowed_lat(),
                                   f"Expected lat: [{expected_lat}] in initial state with controls_allowed: [{controls_allowed}]")

                  # Test transition to opposite state
                  prev_lat = expected_lat  # Remember previous state
                  self.safety.set_controls_allowed(not controls_allowed)
                  self._rx(self._speed_msg(0))
                  # Only enable on rising edge
                  if not controls_allowed and unified_engagement_mode and enable_mads:
                    expected_lat = True
                  else:
                    expected_lat = prev_lat  # Maintain previous state unless rising edge
                  self.assertEqual(expected_lat, self.safety.get_controls_allowed_lat(),
                                   f"Expected lat: [{expected_lat}] after controls_allowed transition [{controls_allowed}] -> [{not controls_allowed}]")

                  # Test transition back to initial state
                  prev_lat = expected_lat  # Remember previous state
                  self.safety.set_controls_allowed(controls_allowed)
                  self._rx(self._speed_msg(0))
                  # Only enable on rising edge
                  if controls_allowed and unified_engagement_mode and enable_mads:
                    expected_lat = True
                  else:
                    expected_lat = prev_lat  # Maintain previous state unless rising edge
                  self.assertEqual(expected_lat, self.safety.get_controls_allowed_lat(),
                                   f"Expected lat: [{expected_lat}] after controls_allowed transition [{not controls_allowed}] -> [{controls_allowed}]")
    finally:
      self._mads_states_cleanup()

  def test_alternative_experience_flag_setting(self):
    """Test setting of alternative experience flags"""
    try:
      self._mads_states_cleanup()

      # Test main_cruise_allowed behavior
      # 1. Set all bits EXCEPT main_cruise_allowed
      self.safety.set_mads_params(True, False, False, True, True)
      self.assertFalse(self.safety.get_main_cruise_allowed(),
                       "main_cruise_allowed should be false when its bit is not set")

      # 2. Set ONLY main_cruise_allowed
      self.safety.set_mads_params(True, False, True, False, False)
      self.assertTrue(self.safety.get_main_cruise_allowed(),
                      "main_cruise_allowed should be true when its bit is set")

      # Test always_allow_mads_button behavior
      # 1. Set all bits EXCEPT always_allow_mads_button
      self.safety.set_mads_params(True, False, True, True, False)
      self.assertFalse(self.safety.get_always_allow_mads_button(),
                       "always_allow_mads_button should be false when its bit is not set")

      # 2. Set ONLY always_allow_mads_button
      self.safety.set_mads_params(True, False, False, False, True)
      self.assertTrue(self.safety.get_always_allow_mads_button(),
                      "always_allow_mads_button should be true when its bit is set")

      # Test zero handling
      # 1. No bits set
      self.safety.set_mads_params(False, False, False, False, False)
      self.assertFalse(self.safety.get_main_cruise_allowed(),
                       "main_cruise_allowed should be false when no bits are set")
      self.assertFalse(self.safety.get_always_allow_mads_button(),
                       "always_allow_mads_button should be false when no bits are set")

      # 2. Only MADS enabled with target bits false
      self.safety.set_mads_params(True, False, False, False, False)
      self.assertFalse(self.safety.get_main_cruise_allowed(),
                       "main_cruise_allowed should be false when only MADS is enabled")
      self.assertFalse(self.safety.get_always_allow_mads_button(),
                       "always_allow_mads_button should be false when only MADS is enabled")

      # Test all combinations for always_allow_mads_button (to catch != vs == mutation)
      test_combinations = [
        (True, False, False, False, False),  # MADS only
        (True, False, True, False, False),   # MADS + cruise
        (True, False, False, True, False),   # MADS + unified
        (True, False, False, False, True),   # MADS + button
        (True, False, True, True, True),     # all enabled
      ]

      for params in test_combinations:
        self.safety.set_mads_params(*params)
        self.assertEqual(params[4], self.safety.get_always_allow_mads_button(),
                         f"always_allow_mads_button mismatch for params {params}")
        self.assertEqual(params[2], self.safety.get_main_cruise_allowed(),
                         f"main_cruise_allowed mismatch for params {params}")

    finally:
      self._mads_states_cleanup()
