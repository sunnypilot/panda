#ifndef MADS_STATE_H
#define MADS_STATE_H

#include <stdbool.h>
#include <stdint.h>

// Enable the ability to enable sunnypilot Automatic Lane Centering and ACC/SCC independently of each other. This
// will enable MADS and allow other features to be used.
// Enable the ability to re-engage sunnypilot Automatic Lane Centering only (NOT ACC/SCC) on brake release while MADS
// is enabled.
#define ALT_EXP_ENABLE_MADS 1024
// Enable the ability to disable disengaging lateral control on brake press while MADS is enabled.
#define ALT_EXP_DISABLE_DISENGAGE_LATERAL_ON_BRAKE 2048

#define MISMATCH_DEFAULT_THRESHOLD 25

extern int temp_debug;
int temp_debug = 0;

// Button transition types
typedef enum {
    BUTTON_NO_CHANGE,
    BUTTON_PRESSED,
    BUTTON_RELEASED
} ButtonTransition;

// MADS System State Struct
typedef struct {
    // System configuration flags
    bool disengage_lateral_on_brake;
    bool vehicle_moving;

    // System-wide enable/disable
    bool system_enabled;

    // Button states with last state tracking
    struct {
        bool current;
        bool last;
        ButtonTransition transition;
        uint32_t press_timestamp;
    } cruise_button, lkas_button;

    // Vehicle condition states
    bool is_braking;
    bool cruise_engaged;

    // Lateral control permission states
    bool controls_allowed_lat;
    bool disengaged_from_brakes;

    // ACC main state tracking
    struct {
        bool current;
        bool previous;
        uint32_t mismatch_count;
        uint32_t mismatch_threshold;
    } acc_main;
} MADSState;

// Global state instance
MADSState _mads_state;

// Determine button transition
ButtonTransition _get_button_transition(bool current, bool last) {
    if (current && !last) return BUTTON_PRESSED;
    if (!current && last) return BUTTON_RELEASED;
    return BUTTON_NO_CHANGE;
}

// Initialize the MADS state
void mads_state_init(void) {
    _mads_state.system_enabled = false;
    _mads_state.disengage_lateral_on_brake = true;
    _mads_state.vehicle_moving = false;

    // Button state initialization
    _mads_state.cruise_button.current = false;
    _mads_state.cruise_button.last = false;
    _mads_state.cruise_button.transition = BUTTON_NO_CHANGE;
    _mads_state.cruise_button.press_timestamp = 0;

    _mads_state.lkas_button.current = false;
    _mads_state.lkas_button.last = false;
    _mads_state.lkas_button.transition = BUTTON_NO_CHANGE;
    _mads_state.lkas_button.press_timestamp = 0;

    // ACC main state initialization
    _mads_state.acc_main.current = false;
    _mads_state.acc_main.previous = false;
    _mads_state.acc_main.mismatch_count = 0;
    _mads_state.acc_main.mismatch_threshold = MISMATCH_DEFAULT_THRESHOLD;

    // Control states
    _mads_state.is_braking = false;
    _mads_state.cruise_engaged = false;
    _mads_state.controls_allowed_lat = false;
    _mads_state.disengaged_from_brakes = false;
    // temp_debug = 99;
}

// Exit lateral controls
void _mads_exit_controls(void) {
    if (_mads_state.controls_allowed_lat) {
        _mads_state.disengaged_from_brakes = true;
        _mads_state.controls_allowed_lat = false;
    }
}

// Resume lateral controls
void _mads_resume_controls(void) {
    if (_mads_state.disengaged_from_brakes) {
        _mads_state.controls_allowed_lat = controls_allowed;
        _mads_state.disengaged_from_brakes = false;
    }
}

// Reset ACC main state with mismatch handling
void _mads_reset_acc_main(bool acc_main_tx) {
    if (_mads_state.acc_main.current && !acc_main_tx) {
        _mads_state.acc_main.mismatch_count++;
        
        if (_mads_state.acc_main.mismatch_count >= _mads_state.acc_main.mismatch_threshold) {
            _mads_state.acc_main.current = acc_main_tx;
            
            // Update lateral control based on ACC main state
            if (!acc_main_tx) {
                _mads_state.controls_allowed_lat = false;
            }
        }
    } else {
        _mads_state.acc_main.mismatch_count = 0;
    }
}

// Check braking condition
void _mads_check_braking(bool is_braking, bool was_braking) {
    if (is_braking && (!was_braking || _mads_state.vehicle_moving)) {
        _mads_state.controls_allowed_lat = false;
        
        if (_mads_state.disengage_lateral_on_brake) {
            _mads_exit_controls();
        }
    } else if (!is_braking && _mads_state.disengage_lateral_on_brake) {
        _mads_resume_controls();
    }
}

// Update state based on input conditions
void mads_state_update(bool cruise_button, bool lkas_button, bool is_braking, bool cruise_engaged, bool acc_main, bool vehicle_moving) {
    _mads_state.vehicle_moving = vehicle_moving;

    // Update button states
    _mads_state.cruise_button.last = _mads_state.cruise_button.current;
    _mads_state.cruise_button.current = cruise_button;
    _mads_state.cruise_button.transition = _get_button_transition(
        _mads_state.cruise_button.current, 
        _mads_state.cruise_button.last
    );

    // Track button press timestamps
    if (_mads_state.cruise_button.transition == BUTTON_PRESSED) {
        _mads_state.cruise_button.press_timestamp = microsecond_timer_get();
    }

    _mads_state.lkas_button.last = _mads_state.lkas_button.current;
    _mads_state.lkas_button.current = lkas_button;
    _mads_state.lkas_button.transition = _get_button_transition(
        _mads_state.lkas_button.current, 
        _mads_state.lkas_button.last
    );

    // Track button press timestamps
    if (_mads_state.lkas_button.transition == BUTTON_PRESSED) {
        _mads_state.lkas_button.press_timestamp = microsecond_timer_get();
    }

    // Update ACC main state
    _mads_state.acc_main.previous = _mads_state.acc_main.current;
    _mads_state.acc_main.current = acc_main;

    // Check ACC main state and braking conditions
    _mads_reset_acc_main(acc_main);
    _mads_check_braking(is_braking, _mads_state.is_braking);

    // Update other states
    _mads_state.is_braking = is_braking;
    _mads_state.cruise_engaged = cruise_engaged;

    // Determine lateral control permission
    if (!_mads_state.system_enabled) {
        _mads_state.controls_allowed_lat = false;
        return;
    }

    // Lateral control rules with momentary button press logic
    _mads_state.controls_allowed_lat = (
        cruise_engaged &&                   // Cruise control engaged
        !is_braking &&                      // Not braking
        (_mads_state.cruise_button.transition == BUTTON_PRESSED ||
         _mads_state.lkas_button.transition == BUTTON_PRESSED)  // Momentary button press
    );
}

// Global system enable/disable
void mads_set_system_state(bool enabled, bool disengage_lateral_on_brake) {
    mads_state_init();
    _mads_state.system_enabled = enabled;
    _mads_state.disengage_lateral_on_brake = disengage_lateral_on_brake;
}

// Check if lateral control is currently allowed
bool mads_is_lateral_control_allowed(void) {
    // Note: controls_allowed is defined on safety.h and it's available to us by c magic.
    if (_mads_state.system_enabled) {
        return controls_allowed || _mads_state.controls_allowed_lat;
    }
    return controls_allowed;
}

#endif // MADS_STATE_H