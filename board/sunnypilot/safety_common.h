#pragma once

void mads_set_state(bool state) {
  controls_allowed_lat = state;
  disengaged_from_brakes = state;
}

void mads_check_acc_main(void) {
  if (acc_main_on && enable_mads) {
    controls_allowed_lat = true;
  }

  if (!acc_main_on && acc_main_on_prev) {
    controls_allowed = false;
    mads_set_state(false);
  }
  acc_main_on_prev = acc_main_on;
}

void mads_check_lkas_button(void) {
  if (lkas_button && enable_mads) {
    controls_allowed_lat = true;
  }
}

void mads_exit_controls(void) {
  if (controls_allowed_lat) {
    disengaged_from_brakes = true;
    controls_allowed_lat = false;
  }
}

void mads_resume_controls(void) {
  if (disengaged_from_brakes) {
    controls_allowed_lat = true;
    disengaged_from_brakes = false;
  }
}

void check_braking_condition(bool state, bool state_prev) {
  if (state && (!state_prev || vehicle_moving)) {
    controls_allowed = false;
    if (disengage_lateral_on_brake) {
      mads_exit_controls();
    }
  } else if (!state && disengage_lateral_on_brake) {
    mads_resume_controls();
  } else {
  }
}
