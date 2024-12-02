#ifndef MADS_STATE_H
#define MADS_STATE_H

#include <stdbool.h>
#include <stdint.h>

// Flags meant to be set by each specific safety_{make}
#define BUTTON_UNINITIALIZED (-1)
extern int main_button_prev;
int main_button_prev = BUTTON_UNINITIALIZED;

extern int lkas_button_prev;
int lkas_button_prev = BUTTON_UNINITIALIZED;
// --

// Enable the ability to enable sunnypilot Automatic Lane Centering and ACC/SCC independently of each other. This
// will enable MADS and allow other features to be used.
// Enable the ability to re-engage sunnypilot Automatic Lane Centering only (NOT ACC/SCC) on brake release while MADS
// is enabled.
#define ALT_EXP_ENABLE_MADS 1024
// Enable the ability to disable disengaging lateral control on brake press while MADS is enabled.
#define ALT_EXP_DISABLE_DISENGAGE_LATERAL_ON_BRAKE 2048

#define MISMATCH_DEFAULT_THRESHOLD 25
#define MADS_STATE_FLAG_DEFAULT 0U
#define MADS_STATE_FLAG_RESERVED 1U
#define MADS_STATE_FLAG_MAIN_BUTTON_AVAILABLE 2U
#define MADS_STATE_FLAG_LKAS_BUTTON_AVAILABLE 4U


// Button transition types
typedef enum {
    MADS_BUTTON_NO_CHANGE,
    MADS_BUTTON_PRESSED,
    MADS_BUTTON_RELEASED
} ButtonTransition;

// MADS System State Struct
typedef struct {
    uint32_t state_flags;

    // Values from stock that we need
    const bool *is_vehicle_moving_ptr;

    // System configuration flags
    bool disengage_lateral_on_brake;

    // System-wide enable/disable
    bool system_enabled;

    // Button states with last state tracking
    struct {
        const int *current;
        int last;
        ButtonTransition transition;
        uint32_t press_timestamp;
        bool is_engaged;
    } main_button;

    struct {
        const int *current;
        int last;
        ButtonTransition transition;
        uint32_t press_timestamp;
        bool is_engaged;
    } lkas_button; // Rule 12.3: separate declarations

    // Vehicle condition states
    bool is_braking;
    bool cruise_engaged;

    // Lateral control permission states
    bool controls_allowed_lat;
    bool disengaged_from_brakes;

    // ACC main state tracking
    struct {
        const bool * current;
        bool previous;
        uint32_t mismatch_count;
        uint32_t mismatch_threshold;
    } acc_main;
} MADSState;

// Global state instance
static MADSState _mads_state; // Rule 8.4: static for internal linkage

// Determine button transition
static ButtonTransition _get_button_transition(bool current, bool last) {
    ButtonTransition result = MADS_BUTTON_NO_CHANGE;
    
    if (current && !last) {
        result = MADS_BUTTON_PRESSED;
    } else if (!current && last) {
        result = MADS_BUTTON_RELEASED;
    } else {
        result = MADS_BUTTON_NO_CHANGE;
    }
    
    return result;
}

// Initialize the MADS state
static void mads_state_init(void) {
    _mads_state.is_vehicle_moving_ptr = NULL;
    _mads_state.acc_main.current = NULL;
    _mads_state.main_button.current = &main_button_prev;
    _mads_state.lkas_button.current = &lkas_button_prev;
    _mads_state.state_flags = MADS_STATE_FLAG_DEFAULT;

    _mads_state.system_enabled = false;
    _mads_state.disengage_lateral_on_brake = true;

    // Button state initialization
    _mads_state.main_button.last = BUTTON_UNINITIALIZED;
    _mads_state.main_button.transition = MADS_BUTTON_NO_CHANGE;
    _mads_state.main_button.press_timestamp = 0;
    _mads_state.main_button.is_engaged = false;

    _mads_state.lkas_button.last = BUTTON_UNINITIALIZED;
    _mads_state.lkas_button.transition = MADS_BUTTON_NO_CHANGE;
    _mads_state.lkas_button.press_timestamp = 0;
    _mads_state.lkas_button.is_engaged = false;

    // ACC main state initialization
    _mads_state.acc_main.previous = false;
    _mads_state.acc_main.mismatch_count = 0;
    _mads_state.acc_main.mismatch_threshold = MISMATCH_DEFAULT_THRESHOLD;

    // Control states
    _mads_state.is_braking = false;
    _mads_state.cruise_engaged = false;
    _mads_state.controls_allowed_lat = false;
    _mads_state.disengaged_from_brakes = false;
}

// Exit lateral controls
static void _mads_exit_controls(void) {
    if (_mads_state.controls_allowed_lat) {
        _mads_state.disengaged_from_brakes = true;
        _mads_state.controls_allowed_lat = false;
    }
}

// Resume lateral controls
static void _mads_resume_controls(void) {
    if (_mads_state.disengaged_from_brakes) {
        _mads_state.controls_allowed_lat = true;
        _mads_state.disengaged_from_brakes = false;
    }
}

// // Reset ACC main state with mismatch handling
// static void _mads_reset_acc_main(bool acc_main_tx) {
//     if (_mads_state.acc_main.current && !acc_main_tx) {
//         _mads_state.acc_main.mismatch_count++;
//
//         if (_mads_state.acc_main.mismatch_count >= _mads_state.acc_main.mismatch_threshold) {
//             _mads_state.acc_main.current = acc_main_tx;
//
//             // Update lateral control based on ACC main state
//             _mads_state.controls_allowed_lat = false;
//         }
//     } else {
//         _mads_state.acc_main.mismatch_count = 0;
//     }
// }

// Check braking condition
static void _mads_check_braking(bool is_braking) {
    bool was_braking = _mads_state.is_braking;
    if (is_braking && (!was_braking || *_mads_state.is_vehicle_moving_ptr) && _mads_state.disengage_lateral_on_brake) {
        _mads_exit_controls();
    }

    if (!is_braking && _mads_state.disengage_lateral_on_brake) {
        _mads_resume_controls();
    }
    _mads_state.is_braking = is_braking;
}

// Update state based on input conditions
void mads_state_update(const bool *op_vehicle_moving, const bool *op_acc_main, bool is_braking, bool cruise_engaged) {
    if (_mads_state.is_vehicle_moving_ptr == NULL) {
        _mads_state.is_vehicle_moving_ptr = op_vehicle_moving;
    }

    if (_mads_state.acc_main.current == NULL) {
        _mads_state.acc_main.current = op_acc_main;
    }

    // Update button states
    if (main_button_prev != BUTTON_UNINITIALIZED) {
        _mads_state.state_flags |= MADS_STATE_FLAG_MAIN_BUTTON_AVAILABLE;
        _mads_state.main_button.current = &main_button_prev;
        _mads_state.main_button.transition = _get_button_transition(
            *_mads_state.main_button.current > 0,
            _mads_state.main_button.last > 0
        );
        
        // Engage on press, disengage on press if already pressed
        if (_mads_state.main_button.transition == MADS_BUTTON_PRESSED) {
            if (_mads_state.main_button.is_engaged) {
                _mads_state.main_button.is_engaged = false;  // Disengage if already engaged
            } else {
                _mads_state.main_button.is_engaged = true;  // Engage otherwise
            }
        }

        _mads_state.main_button.last = *_mads_state.main_button.current;
    }

    // Same for LKAS button
    if (lkas_button_prev != BUTTON_UNINITIALIZED) {
        _mads_state.state_flags |= MADS_STATE_FLAG_LKAS_BUTTON_AVAILABLE;
        _mads_state.lkas_button.current = &lkas_button_prev;
        _mads_state.lkas_button.transition = _get_button_transition(
            *_mads_state.lkas_button.current > 0,
            _mads_state.lkas_button.last > 0
        );

        if (_mads_state.lkas_button.transition == MADS_BUTTON_PRESSED) {
            if (_mads_state.lkas_button.is_engaged) {
                _mads_state.lkas_button.is_engaged = false;
            } else {
                _mads_state.lkas_button.is_engaged = true;
            }
        }

        _mads_state.lkas_button.last = *_mads_state.lkas_button.current;
    }

    // Update other states
    _mads_state.cruise_engaged = cruise_engaged;

    // Use engagement state for lateral control - prioritize LKAS button if available
    if (lkas_button_prev != BUTTON_UNINITIALIZED) {
        _mads_state.controls_allowed_lat = _mads_state.lkas_button.is_engaged;
    } else {
        _mads_state.controls_allowed_lat = _mads_state.main_button.is_engaged || _mads_state.lkas_button.is_engaged;
    }

    _mads_state.controls_allowed_lat = _mads_state.controls_allowed_lat || *_mads_state.acc_main.current;

    // Check ACC main state and braking conditions
    // _mads_reset_acc_main(acc_main);
    _mads_check_braking(is_braking);

    // Update ACC main state
    _mads_state.acc_main.previous = *_mads_state.acc_main.current;
}

// Global system enable/disable
void mads_set_system_state(bool enabled, bool disengage_lateral_on_brake) {
    mads_state_init();
    _mads_state.system_enabled = enabled;
    _mads_state.disengage_lateral_on_brake = disengage_lateral_on_brake;
}

// Check if lateral control is currently allowed by MADS
bool mads_is_lateral_control_allowed_by_mads(void) {
    return _mads_state.system_enabled && _mads_state.controls_allowed_lat;
}

#endif // MADS_STATE_H
