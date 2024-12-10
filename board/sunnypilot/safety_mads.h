#pragma once

#include "sunnypilot/safety_mads_declarations.h"

// ===============================
// Global Variables
// ===============================

ButtonState mads_button_press = MADS_BUTTON_UNAVAILABLE;
MADSState m_mads_state;

// ===============================
// State Update Helpers
// ===============================

static EdgeTransition m_get_edge_transition(bool current, bool last) {
  EdgeTransition state;

  if (current && !last) {
    state = MADS_EDGE_RISING;
  } else if (!current && last) {
    state = MADS_EDGE_FALLING;
  } else {
    state = MADS_EDGE_NO_CHANGE;
  }

  return state;
}

static void m_mads_state_init(void) {
  m_mads_state.is_vehicle_moving_ptr = NULL;
  m_mads_state.acc_main.current = NULL;
  m_mads_state.mads_button.current = NULL;

  m_mads_state.system_enabled = false;
  m_mads_state.disengage_lateral_on_brake = false;
  m_mads_state.main_cruise_allowed = false;
  m_mads_state.unified_engagement_mode = false;

  m_mads_state.acc_main.previous = false;
  m_mads_state.acc_main.transition = MADS_EDGE_NO_CHANGE;

  m_mads_state.mads_button.last = MADS_BUTTON_UNAVAILABLE;
  m_mads_state.mads_button.transition = MADS_EDGE_NO_CHANGE;


  m_mads_state.current_disengage.reason = MADS_DISENGAGE_REASON_NONE;
  m_mads_state.previous_disengage = m_mads_state.current_disengage;

  m_mads_state.is_braking = false;
  m_mads_state.controls_requested_lat = false;
  m_mads_state.controls_allowed_lat = false;
}

static bool m_can_allow_controls_lat(void) {
  const MADSState *state = get_mads_state();
  bool allowed = false;
  if (state->system_enabled) {
    switch (state->current_disengage.reason) {
      case MADS_DISENGAGE_REASON_BRAKE:
        allowed = !state->is_braking && state->disengage_lateral_on_brake;
        break;
      case MADS_DISENGAGE_REASON_NON_PCM_ACC_MAIN_DESYNC:
      case MADS_DISENGAGE_REASON_ACC_MAIN_OFF:
      case MADS_DISENGAGE_REASON_LAG:
      case MADS_DISENGAGE_REASON_BUTTON:
      case MADS_DISENGAGE_REASON_NONE:
      default:
        allowed = true;
        break;
    }
  }
  return allowed;
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

    button_state->last = *button_state->current;
  }
}

// Main cruise
static void m_update_binary_state(BinaryStateTracking *state) {
  state->transition = m_get_edge_transition(*state->current, state->previous);
  state->previous = *state->current;
}

static void m_mads_try_allow_controls_lat(void) {
  if (m_mads_state.controls_requested_lat && !m_mads_state.controls_allowed_lat && m_can_allow_controls_lat()) {
    m_mads_state.controls_allowed_lat = true;
    m_mads_state.previous_disengage = m_mads_state.current_disengage;
    m_mads_state.current_disengage.reason = MADS_DISENGAGE_REASON_NONE;
  }
}

// Use buttons or main cruise state transition properties to request lateral control
static void m_mads_update_state(void) {
  // Main cruise
  if ((m_mads_state.acc_main.transition == MADS_EDGE_RISING) && m_mads_state.main_cruise_allowed) {
    m_mads_state.controls_requested_lat = true;
  } else if (m_mads_state.acc_main.transition == MADS_EDGE_FALLING) {
    m_mads_state.controls_requested_lat = false;
    mads_exit_controls(MADS_DISENGAGE_REASON_ACC_MAIN_OFF);
  } else {
  }

  // MADS button
  if (m_mads_state.mads_button.transition == MADS_EDGE_RISING) {
    m_mads_state.controls_requested_lat = !m_mads_state.controls_allowed_lat;

    if (!m_mads_state.controls_requested_lat) {
      mads_exit_controls(MADS_DISENGAGE_REASON_BUTTON);
    }
  }

  if ((m_mads_state.op_controls_allowed.transition == MADS_EDGE_RISING) && m_mads_state.unified_engagement_mode) {
    m_mads_state.controls_requested_lat = true;
  }
}

// ===============================
// Function Implementations
// ===============================

inline const MADSState *get_mads_state(void) {
  return &m_mads_state;
}

inline void mads_set_system_state(bool enabled, bool disengage_lateral_on_brake, bool main_cruise_allowed, bool unified_engagement_mode) {
  m_mads_state_init();
  m_mads_state.system_enabled = enabled;
  m_mads_state.disengage_lateral_on_brake = disengage_lateral_on_brake;
  m_mads_state.main_cruise_allowed = main_cruise_allowed;
  m_mads_state.unified_engagement_mode = unified_engagement_mode;
}

inline void mads_exit_controls(DisengageReason reason) {
  if (m_mads_state.controls_allowed_lat) {
    m_mads_state.previous_disengage = m_mads_state.current_disengage;
    m_mads_state.current_disengage.reason = reason;
    m_mads_state.controls_allowed_lat = false;
  }
}

inline bool mads_is_lateral_control_allowed_by_mads(void) {
  return m_mads_state.system_enabled && m_mads_state.controls_allowed_lat;
}

inline void mads_state_update(const bool *op_vehicle_moving, const bool *op_acc_main, const bool *op_allowed, bool is_braking) {
  m_mads_state.is_vehicle_moving_ptr = op_vehicle_moving;
  m_mads_state.acc_main.current = op_acc_main;
  m_mads_state.op_controls_allowed.current = op_allowed;
  m_mads_state.mads_button.current = &mads_button_press;

  m_update_binary_state(&m_mads_state.acc_main);
  m_update_binary_state(&m_mads_state.op_controls_allowed);
  m_update_button_state(&m_mads_state.mads_button);

  m_mads_update_state();

  m_mads_check_braking(is_braking);
  m_mads_try_allow_controls_lat();
}
