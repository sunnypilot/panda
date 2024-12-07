#pragma once

#include "sunnypilot/safety_mads_declarations.h"

// ===============================
// Global Variables
// ===============================

ButtonState main_button_press = MADS_BUTTON_UNAVAILABLE;
ButtonState lkas_button_press = MADS_BUTTON_UNAVAILABLE;
MADSState m_mads_state;

// ===============================
// State Update Helpers
// ===============================

static EdgeTransition m_get_edge_transition(bool current, bool last) {
  EdgeTransition result;

  if (current && !last) {
    result = MADS_EDGE_RISING;
  } else if (!current && last) {
    result = MADS_EDGE_FALLING;
  } else {
    result = MADS_EDGE_NO_CHANGE;
  }

  return result;
}

static void m_mads_state_init(void) {
  m_mads_state.is_vehicle_moving_ptr = NULL;
  m_mads_state.acc_main.current = NULL;
  m_mads_state.main_button.current = NULL;
  m_mads_state.lkas_button.current = NULL;
  m_mads_state.state_flags = MADS_STATE_FLAG_DEFAULT;

  m_mads_state.system_enabled = false;
  m_mads_state.disengage_lateral_on_brake = true;

  m_mads_state.main_button.last = MADS_BUTTON_UNAVAILABLE;
  m_mads_state.main_button.transition = MADS_EDGE_NO_CHANGE;

  m_mads_state.lkas_button.last = MADS_BUTTON_UNAVAILABLE;
  m_mads_state.lkas_button.transition = MADS_EDGE_NO_CHANGE;

  m_mads_state.acc_main.previous = false;

  m_mads_state.current_disengage.reason = MADS_DISENGAGE_REASON_NONE;
  m_mads_state.previous_disengage = m_mads_state.current_disengage;

  m_mads_state.is_braking = false;
  // m_mads_state.cruise_engaged = false;
  m_mads_state.controls_requested_lat = false;
  m_mads_state.controls_allowed_lat = false;
}

static bool m_can_allow_controls_lat(void) {
  const MADSState *state = get_mads_state();
  bool result = false;
  if (state->system_enabled) {
    switch (state->current_disengage.reason) {
      case MADS_DISENGAGE_REASON_BRAKE:
        result = !state->is_braking && state->disengage_lateral_on_brake;
        break;
      case MADS_DISENGAGE_REASON_LAG:
      case MADS_DISENGAGE_REASON_BUTTON:
      case MADS_DISENGAGE_REASON_NONE:
      default:
        result = true;
        break;
    }
  }
  return result;
}

static void m_mads_check_braking(bool is_braking) {
  bool was_braking = m_mads_state.is_braking;
  if (is_braking && (!was_braking || *m_mads_state.is_vehicle_moving_ptr) && m_mads_state.disengage_lateral_on_brake) {
    mads_exit_controls(MADS_DISENGAGE_REASON_BRAKE);
  }
  
  m_mads_state.is_braking = is_braking;
}

static void m_update_button_state(ButtonStateTracking *button_state) {
  if (*button_state->current != MADS_BUTTON_UNAVAILABLE) {
    button_state->transition = m_get_edge_transition(
      *button_state->current == MADS_BUTTON_PRESSED,
      button_state->last == MADS_BUTTON_PRESSED
    );

    if (button_state->transition == MADS_EDGE_RISING) {
      m_mads_state.controls_requested_lat = !m_mads_state.controls_allowed_lat;
      if (!m_mads_state.controls_requested_lat) {
        mads_exit_controls(MADS_DISENGAGE_REASON_BUTTON);
      }
    }

    button_state->last = *button_state->current;
  }
}

static void m_update_binary_state(BinaryStateTracking *state) {
  EdgeTransition transition = m_get_edge_transition(*state->current, state->previous);
  if (transition == MADS_EDGE_RISING) {
    m_mads_state.controls_requested_lat = true;
  } else if (transition == MADS_EDGE_FALLING) {
    mads_exit_controls(MADS_DISENGAGE_REASON_ACC_MAIN_OFF);
  } else {
    // Do nothing
  }

  state->previous = *state->current;
}

static void m_mads_try_allow_controls_lat(void) {
  if (m_mads_state.controls_requested_lat && !m_mads_state.controls_allowed_lat && m_can_allow_controls_lat()) {
    m_mads_state.controls_allowed_lat = true;
    m_mads_state.previous_disengage = m_mads_state.current_disengage;
    m_mads_state.current_disengage.reason = MADS_DISENGAGE_REASON_NONE;
  }
}

// ===============================
// Function Implementations
// ===============================

inline const MADSState* get_mads_state(void) {
  return &m_mads_state;
}

inline void mads_set_system_state(bool enabled, bool disengage_lateral_on_brake) {
  m_mads_state_init();
  m_mads_state.system_enabled = enabled;
  m_mads_state.disengage_lateral_on_brake = disengage_lateral_on_brake;
}

inline void mads_exit_controls(DisengageReason reason) {
  if (reason == MADS_DISENGAGE_REASON_ACC_MAIN_OFF) {
    m_mads_state.controls_requested_lat = false;
  }
  
  if (m_mads_state.controls_allowed_lat) {
    m_mads_state.previous_disengage = m_mads_state.current_disengage;
    m_mads_state.current_disengage.reason = reason;
    m_mads_state.controls_allowed_lat = false;
  }
}

inline bool mads_is_lateral_control_allowed_by_mads(void) {
  return m_mads_state.system_enabled && m_mads_state.controls_allowed_lat;
}

inline void mads_state_update(const bool *op_vehicle_moving, const bool *op_acc_main, bool is_braking, bool cruise_engaged) {
  m_mads_state.is_vehicle_moving_ptr = op_vehicle_moving;
  m_mads_state.acc_main.current = op_acc_main;
  m_mads_state.main_button.current = &main_button_press;
  m_mads_state.lkas_button.current = &lkas_button_press;

  if (!(m_mads_state.state_flags & MADS_STATE_FLAG_MAIN_BUTTON_AVAILABLE) && (main_button_press != MADS_BUTTON_UNAVAILABLE)) {
    m_mads_state.state_flags |= MADS_STATE_FLAG_MAIN_BUTTON_AVAILABLE;
  }

  if (!(m_mads_state.state_flags & MADS_STATE_FLAG_LKAS_BUTTON_AVAILABLE) && (lkas_button_press != MADS_BUTTON_UNAVAILABLE)) {
    m_mads_state.state_flags |= MADS_STATE_FLAG_LKAS_BUTTON_AVAILABLE;
  }

  m_update_button_state(&m_mads_state.main_button);
  m_update_button_state(&m_mads_state.lkas_button);
  m_update_binary_state(&m_mads_state.acc_main);

  //TODO-SP: Should we use this?
  UNUSED(cruise_engaged);
  // m_mads_state.cruise_engaged = cruise_engaged;
  m_mads_check_braking(is_braking);
  m_mads_try_allow_controls_lat();
}
