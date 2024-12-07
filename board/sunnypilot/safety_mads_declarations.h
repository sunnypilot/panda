#pragma once

// ===============================
// Type Definitions and Enums
// ===============================

typedef enum __attribute__((packed)) {
  MADS_BUTTON_UNAVAILABLE = -1,
  MADS_BUTTON_NOT_PRESSED = 0,
  MADS_BUTTON_PRESSED = 1
} ButtonState;

typedef enum __attribute__((packed)) {
  MADS_EDGE_NO_CHANGE = 0,
  MADS_EDGE_RISING = 1,
  MADS_EDGE_FALLING = 2
} EdgeTransition;

typedef enum __attribute__((packed)) {
  MADS_DISENGAGE_REASON_NONE = 0,
  MADS_DISENGAGE_REASON_BRAKE = 1,
  MADS_DISENGAGE_REASON_LAG = 2,
  MADS_DISENGAGE_REASON_BUTTON = 3,
  MADS_DISENGAGE_REASON_ACC_MAIN_OFF = 4
} DisengageReason;

// ===============================
// Constants and Defines
// ===============================

#define ALT_EXP_ENABLE_MADS 1024
#define ALT_EXP_DISABLE_DISENGAGE_LATERAL_ON_BRAKE 2048

#define MISMATCH_DEFAULT_THRESHOLD 25
#define MADS_STATE_FLAG_DEFAULT 0U
#define MADS_STATE_FLAG_RESERVED 1U
#define MADS_STATE_FLAG_MAIN_BUTTON_AVAILABLE 2U
#define MADS_STATE_FLAG_LKAS_BUTTON_AVAILABLE 4U

// ===============================
// Data Structures
// ===============================

typedef struct {
  DisengageReason reason;
  bool can_auto_resume;
} DisengageState;

typedef struct {
  const ButtonState *current;
  ButtonState last;
  EdgeTransition transition;
} ButtonStateTracking;

typedef struct {
  EdgeTransition transition;
  const bool *current;
  bool previous : 1;
} BinaryStateTracking;

typedef struct {
  uint32_t state_flags;
  const bool *is_vehicle_moving_ptr;

  ButtonStateTracking main_button;
  ButtonStateTracking lkas_button;
  BinaryStateTracking acc_main;

  DisengageState current_disengage;
  DisengageState previous_disengage;

  bool system_enabled : 1;
  bool disengage_lateral_on_brake : 1;
  bool is_braking : 1;
  // bool cruise_engaged : 1;
  bool controls_requested_lat : 1;
  bool controls_allowed_lat : 1;
} MADSState;

// ===============================
// Global Variables
// ===============================

extern ButtonState main_button_press;
extern ButtonState lkas_button_press;
extern MADSState m_mads_state;

// ===============================
// External Function Declarations (kept as needed)
// ===============================

extern const MADSState* get_mads_state(void);
extern void mads_set_system_state(bool enabled, bool disengage_lateral_on_brake);
extern void mads_state_update(const bool *op_vehicle_moving, const bool *op_acc_main, bool is_braking, bool cruise_engaged);
extern void mads_exit_controls(DisengageReason reason);
extern bool mads_is_lateral_control_allowed_by_mads(void);
