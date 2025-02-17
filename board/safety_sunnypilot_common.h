#ifndef SAFETY_SUNNYPILOT_COMMON_H
#define SAFETY_SUNNYPILOT_COMMON_H

void mads_acc_main_check(const bool main_on) {
  if (main_on && mads_enabled) {
    controls_allowed = true;
  }
  if (!main_on && acc_main_on_prev) {
    disengageFromBrakes = false;
    controls_allowed = false;
    controls_allowed_long = false;
  }
  acc_main_on_prev = main_on;
}

void mads_lkas_button_check(const bool lkas_pressed) {
  if (lkas_pressed && !lkas_pressed_prev) {
    controls_allowed = true;
  }
  lkas_pressed_prev = lkas_pressed;
}

void mads_exit_controls_check(void) {
  if (alternative_experience & ALT_EXP_MADS_DISABLE_DISENGAGE_LATERAL_ON_BRAKE) {
    disengageFromBrakes = true;
    controls_allowed_long = false;
  } else {
    if ((alternative_experience & ALT_EXP_ENABLE_MADS) && controls_allowed) {
      disengageFromBrakes = true;
    }
    controls_allowed = false;
    controls_allowed_long = false;
  }
}

void mads_resume_controls_check(void) {
  disengageFromBrakes = false;
  if (alternative_experience & ALT_EXP_ENABLE_MADS) {
    controls_allowed = true;
  }
}

typedef struct {
  uint8_t fca_cmd_act;
  uint8_t aeb_cmd_act;
  uint8_t cf_vsm_warn_fca11;
  uint8_t cf_vsm_warn_scc12;
  uint8_t cf_vsm_deccmdact_scc12;
  uint8_t cf_vsm_deccmdact_fca11;
  uint8_t cr_vsm_deccmd_scc12;
  uint8_t cr_vsm_deccmd_fca11;
  uint8_t obj_valid;
  uint8_t acc_objstatus;
  uint8_t acc_obj_lat_pos_1;
  uint8_t acc_obj_lat_pos_2;
  uint8_t acc_obj_dist_1;
  uint8_t acc_obj_dist_2;
  uint8_t acc_obj_rel_spd_1;
  uint8_t acc_obj_rel_spd_2;
} ESCC_Msg;

void send_escc_msg(const ESCC_Msg *msg, int bus_number);

#endif
