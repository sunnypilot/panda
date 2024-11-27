from abc import abstractmethod


class MadsCommonBase:
    @abstractmethod
    def _lkas_button_msg(self, enabled):
        raise NotImplementedError

    @abstractmethod
    def _acc_state_msg(self, enabled):
        raise NotImplementedError

    @abstractmethod
    def _mads_engage_msg(self, enabled):
        raise NotImplementedError

    def _test_lat_enabled_when_msg(self, msg, expected_enabled):
        self.safety.set_controls_allowed_lat(False)
        self._rx(msg)
        self.assertEqual(
            expected_enabled, self.safety.get_controls_allowed_lat(),
            (
                "mads expected [{}] | was [{}]. ".format(expected_enabled, self.safety.get_enable_mads()) +
                "acc_main_on [{}]. ".format(self.safety.get_acc_main_on()) +
                "alternative_experience [{}]. ".format(self.safety.get_alternative_experience()) +
                "controls_allowed [{}]. ".format(self.safety.get_controls_allowed()) +
                "lkas_main_on [{}]. ".format(self.safety.get_lkas_main_on()) +
                "hyundai_longitudinal [{}].".format(self.safety.get_hyundai_longitudinal())
            )
        )

    #TODO-SP: We must also test disengagements. Right now we only really "validate" that we've engaged MADS under the conditions.

    def test_main_cruise_allows_lateral_control_when_mads_enabled(self):
        self._test_enable_lateral_control(True, True, True)

    def test_main_cruise_prevents_lateral_control_when_mads_disabled(self):
        self._test_enable_lateral_control(False, True, False)

    def test_non_main_cruise_prevents_lateral_control_when_mads_enabled(self):
        self._test_enable_lateral_control(True, False, False)

    def _test_enable_lateral_control(self, mads_enabled, valid_mads_engage, expected_enabled):
        self.safety.set_enable_mads(mads_enabled)
        self._test_lat_enabled_when_msg(self._mads_engage_msg(valid_mads_engage), expected_enabled)
        self.safety.set_enable_mads(False)


    #TODO-SP: NOTE: Technically speaking, we don't need to test for specific "LKAS" buttons unless we want to support MADS engagement
    #  via both LKAS button + Main button. So far what I saw is that we really have them separate when there's 2 buttons.

    # def test_lkas_button_allows_lateral_control_when_mads_enabled(self):
    #     self.safety.set_alternative_experience(ALTERNATIVE_EXPERIENCE.ENABLE_MADS)
    #     self._test_lkas_button(True)
    #
    # def test_lkas_button_allows_lateral_control_when_mads_disabled(self):
    #     self.safety.set_alternative_experience(ALTERNATIVE_EXPERIENCE.DEFAULT)
    #     self._test_lkas_button(False)
    #
    # def _test_lkas_button(self, mads_enabled):
    #     self._test_lat_enabled_when_msg(self._lkas_button_msg(), mads_enabled)
    #     self.safety.set_alternative_experience(ALTERNATIVE_EXPERIENCE.DEFAULT)
    #
