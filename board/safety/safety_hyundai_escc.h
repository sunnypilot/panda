#pragma once

#define DEVNULL_BUS (-1)
#define CAR_BUS 0
#define RADAR_BUS 2

bool scc_block_allowed = false;
uint32_t sunnypilot_detected_last = 0;

// Initialize bytes to send to 2AB
ESCC_Msg escc = {0};

static void escc_rx_hook(const CANPacket_t* to_push) {
  const int bus = GET_BUS(to_push);
  const int addr = GET_ADDR(to_push);
  

  const int is_scc_msg = addr == 0x420 || addr == 0x421 || addr == 0x50A || addr == 0x389;
  const int is_fca_msg = addr == 0x38D || addr == 0x483;
#ifdef DEBUG
  print("escc_rx_hook: "); putui(bus); print(" - "); puth4(addr); print(" is_scc_msg: "); print(is_scc_msg?"yes":"no"); print(" is_fca_msg: "); print(is_fca_msg?"yes":"no"); print("\n");
#endif

  if (bus == RADAR_BUS && (is_scc_msg || is_fca_msg)) {
    switch (addr) {
      // This messsage is blocked if scc_block_allowed is true, and ESCC is updated with the data and sent to sunnypilot
      case 0x420: // SCC11: Forward radar points to sunnypilot
        escc.obj_valid = (GET_BYTE(to_push, 2) & 0x1U);
        escc.acc_objstatus = ((GET_BYTE(to_push, 2) >> 6) & 0x3U);
        escc.acc_obj_lat_pos_1 = GET_BYTE(to_push, 3);
        escc.acc_obj_lat_pos_2 = (GET_BYTE(to_push, 4) & 0x1U);
        escc.acc_obj_dist_1 = ((GET_BYTE(to_push, 4) >> 1) & 0x7FU);
        escc.acc_obj_dist_2 = (GET_BYTE(to_push, 5) & 0xFU);
        escc.acc_obj_rel_spd_1 = ((GET_BYTE(to_push, 5) >> 4) & 0xFU);
        escc.acc_obj_rel_spd_2 = GET_BYTE(to_push, 6);
        send_escc_msg(&escc, CAR_BUS);
        break;

      // This messsage is blocked if scc_block_allowed is true, and ESCC is updated with the data and sent to sunnypilot
      case 0x421: // SCC12: Detect AEB, get the data and write it on the next ESCC msg to sunnypilot.
        escc.aeb_cmd_act = GET_BYTE(to_push, 6) >> 6 & 1U;
        escc.cf_vsm_warn_scc12 = GET_BYTE(to_push, 0) >> 4 & 0x3U;
        escc.cf_vsm_deccmdact_scc12 = GET_BYTE(to_push, 0) >> 1 & 1U;
        escc.cr_vsm_deccmd_scc12 = GET_BYTE(to_push, 2);
        break;

      // This message is not blocked, and is sent straight to the car.
      case 0x38D: // FCA11: Detect AEB, get the data and write it on the next ESCC msg to sunnypilot
        escc.fca_cmd_act = GET_BYTE(to_push, 2) >> 4 & 1U;
        escc.cf_vsm_warn_fca11 = GET_BYTE(to_push, 0) >> 3 & 0x3U;
        escc.cf_vsm_deccmdact_fca11 = GET_BYTE(to_push, 3) >> 7 & 1U;
        escc.cr_vsm_deccmd_fca11 = GET_BYTE(to_push, 1);
        break;

      default: ;
    }
  }
}

static bool escc_tx_hook(const CANPacket_t* to_send) {
#ifdef DEBUG
  const int target_bus = GET_BUS(to_send);
  const int addr = GET_ADDR(to_send);
  print("escc_tx_hook: "); putui(target_bus); print(" - "); puth4(addr); print("\n");
  #else
  UNUSED(to_send);
  #endif
  return true;
}

static int escc_fwd_hook(const int bus_src, const int addr) {
#ifdef DEBUG
  print("escc_fwd_hook: "); putui(bus_src); print(" - "); puth4(addr); print(" scc_block_allowed: "); print(scc_block_allowed?"yes":"no" ); print("\n");
#endif
  // SCC messages are SCC11 (0x420), SCC12 (0x421), SCC13 (0x50A), SCC14 (0x389) 
  const int is_scc_msg = addr == 0x420 || addr == 0x421 || addr == 0x50A || addr == 0x389;

  const uint32_t ts = MICROSECOND_TIMER->CNT;

  // Update the last detected timestamp if an SCC message is from CAR_BUS
  if (bus_src == CAR_BUS && is_scc_msg) {
    sunnypilot_detected_last = ts;
  }

  // Default forwarding logic
  int bus_dst = (bus_src == CAR_BUS) ? RADAR_BUS : CAR_BUS;

  // Update the scc_block_allowed status based on elapsed time
  const uint32_t ts_elapsed = get_ts_elapsed(ts, sunnypilot_detected_last);
  scc_block_allowed = (ts_elapsed <= 150000);

  // If we are allowed to block, and this is an scc msg coming from radar (or somehow we are sending it TO the radar) we block
  if (scc_block_allowed && is_scc_msg && (bus_src == RADAR_BUS || bus_dst == RADAR_BUS))
    bus_dst = DEVNULL_BUS;

  return bus_dst;
}

const safety_hooks hyundai_escc_hooks = {
  .init = alloutput_init,
  .rx = escc_rx_hook,
  .tx = escc_tx_hook,
  .fwd = escc_fwd_hook,
  .get_counter = hyundai_get_counter,
  .get_checksum = hyundai_get_checksum,
  .compute_checksum = hyundai_compute_checksum,
};
