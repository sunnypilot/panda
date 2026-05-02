#ifndef SAFETY_SUNNYPILOT_COMMON_H
#define SAFETY_SUNNYPILOT_COMMON_H

#include <stdint.h>

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
