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
  MADS_DISENGAGE_REASON_ACC_MAIN_OFF = 4,
  MADS_DISENGAGE_REASON_NON_PCM_ACC_MAIN_DESYNC = 5,
} DisengageReason;

// ===============================
// Constants and Defines
// ===============================

#define ALT_EXP_ENABLE_MADS 1024
#define ALT_EXP_DISABLE_DISENGAGE_LATERAL_ON_BRAKE 2048
#define ALT_EXP_MAIN_CRUISE_ALLOWED 4096
#define ALT_EXP_UNIFIED_ENGAGEMENT_MODE 8192

#define MISMATCH_DEFAULT_THRESHOLD 25

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
  const bool *is_vehicle_moving_ptr;

  ButtonStateTracking mads_button;
  BinaryStateTracking acc_main;
  BinaryStateTracking op_controls_allowed;

  DisengageState current_disengage;
  DisengageState previous_disengage;

  bool system_enabled : 1;
  bool disengage_lateral_on_brake : 1;
  bool main_cruise_allowed : 1;
  bool unified_engagement_mode : 1;
  bool is_braking : 1;
  bool controls_requested_lat : 1;
  bool controls_allowed_lat : 1;
} MADSState;

// ===============================
// Global Variables
// ===============================

extern ButtonState mads_button_press;
extern MADSState m_mads_state;

// ===============================
// External Function Declarations (kept as needed)
// ===============================

extern const MADSState* get_mads_state(void);
extern void mads_set_system_state(bool enabled, bool disengage_lateral_on_brake, bool main_cruise_allowed, bool unified_engagement_mode);
extern void mads_state_update(const bool *op_vehicle_moving, const bool *op_acc_main, const bool *op_allowed, bool is_braking);
extern void mads_exit_controls(DisengageReason reason);
extern bool mads_is_lateral_control_allowed_by_mads(void);
