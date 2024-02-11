static uint8_t fca_compute_checksum(CAN_FIFOMailBox_TypeDef *to_push) {
  /* This function does not want the checksum byte in the input data.
  jeep chrysler canbus checksum from http://illmatics.com/Remote%20Car%20Hacking.pdf */
  uint8_t checksum = 0xFF;
  int len = GET_LEN(to_push);
  for (int j = 0; j < (len - 1); j++) {
    uint8_t shift = 0x80;
    uint8_t curr = (uint8_t)GET_BYTE(to_push, j);
    for (int i=0; i<8; i++) {
      uint8_t bit_sum = curr & shift;
      uint8_t temp_chk = checksum & 0x80U;
      if (bit_sum != 0U) {
        bit_sum = 0x1C;
        if (temp_chk != 0U) {
          bit_sum = 1;
        }
        checksum = checksum << 1;
        temp_chk = checksum | 1U;
        bit_sum ^= temp_chk;
      } else {
        if (temp_chk != 0U) {
          bit_sum = 0x1D;
        }
        checksum = checksum << 1;
        bit_sum ^= checksum;
      }
      checksum = bit_sum;
      shift = shift >> 1;
    }
  }
  return ~checksum;
}

static void send_steer_enable_speed(CAN_FIFOMailBox_TypeDef *to_fwd){
  int crc;
  int kph_factor = 128;
  int eps_cutoff_speed;
  int lkas_enable_speed = 65 * kph_factor;
  int apa_enable_speed = 0 * kph_factor;
  int veh_speed = GET_BYTE(to_fwd, 4) | GET_BYTE(to_fwd, 5) << 8;

  eps_cutoff_speed = veh_speed;

  if(steer_type == 2) {
    eps_cutoff_speed = apa_enable_speed >> 8 | ((apa_enable_speed << 8) & 0xFFFF);  //2kph with 128 factor
  }
  else if (steer_type == 1) {
    eps_cutoff_speed = lkas_enable_speed >> 8 | ((lkas_enable_speed << 8) & 0xFFFF);  //65kph with 128 factor
  }

  to_fwd->RDHR &= 0x00FF0000;  //clear speed and Checksum
  to_fwd->RDHR |= eps_cutoff_speed;       //replace speed
  crc = fca_compute_checksum(to_fwd);
  to_fwd->RDHR |= (((crc << 8) << 8) << 8);   //replace Checksum
};

static void send_trans_apa_signature(CAN_FIFOMailBox_TypeDef *to_fwd){
  int gear_R = 0xB;
  if (steer_type == 2) {
    to_fwd->RDLR &= 0xFFFFF0FF;  //clear speed and Checksum
    to_fwd->RDLR |= gear_R << 8;  //replace gear
  }
}
static void send_shifter_apa_signature(CAN_FIFOMailBox_TypeDef *to_fwd){
  int shifter_R = 0x1;
  if (steer_type == 2) {
    to_fwd->RDLR &= 0xFFFFFFE0;  //clear speed and Checksum
    to_fwd->RDLR |= shifter_R << 2;  //replace shifter
  }
}

static void send_rev_apa_signature(CAN_FIFOMailBox_TypeDef *to_fwd){
  if (steer_type == 2) {
    to_fwd->RDLR &= 0xFFFFFFEF;  //clear REV and Checksum
  }
}

static void send_wspd_apa_signature(CAN_FIFOMailBox_TypeDef *to_fwd){
  if (steer_type == 2) {
    to_fwd->RDLR &= 0x00000000;  //clear speed and Checksum
  }
}

static void send_count_apa_signature(CAN_FIFOMailBox_TypeDef *to_fwd){
  if (steer_type == 2) {
    to_fwd->RDLR &= 0x00000000;  //clear speed and Checksum
    to_fwd->RDHR &= 0x00000000;  //clear speed and Checksum
  }
}

static void send_xxx_apa_signature(CAN_FIFOMailBox_TypeDef *to_fwd){
  to_fwd->RDLR &= 0x00000000;  //clear speed and Checksum
}

static void send_apa_signature(CAN_FIFOMailBox_TypeDef *to_fwd){
  int crc;
  int multi = 4; // steering torq multiplier
  int apa_torq = ((lkas_torq - 1024) * multi/4) + 1024;  //LKAS torq 768 to 1280 +-0.5NM  512  //APA torq 896 to 1152 +-1NM 128 0x80

  if ((steer_type == 2) && is_op_active) {
    to_fwd->RDLR &= 0x00000000;  //clear everything for new apa
    to_fwd->RDLR |= 0x50;  //replace apa req to true
    to_fwd->RDLR |= 0x20 << 8 << 8;  //replace apa type = 1
    to_fwd->RDLR |= apa_torq >> 8;  //replace torq
    to_fwd->RDLR |= (apa_torq & 0xFF) << 8;  //replace torq
  }
  to_fwd->RDHR &= 0x00FF0000;  //clear everything except counter
  crc = fca_compute_checksum(to_fwd);
  to_fwd->RDHR |= (((crc << 8) << 8) << 8);   //replace Checksum
};

static void send_acc_decel_msg(CAN_FIFOMailBox_TypeDef *to_fwd){
  int crc;

  if (is_oplong_enabled && !org_collision_active) {
    to_fwd->RDLR &= 0x00000000;
    to_fwd->RDHR &= 0x00FD0080; // keep the counter

    to_fwd->RDLR |= acc_stop << 5;
    to_fwd->RDLR |= acc_go << 6;
    to_fwd->RDLR |= ((acc_decel_cmd >> 8) << 8) << 8;
    to_fwd->RDLR |= ((acc_available << 8) << 8) << 4;
    to_fwd->RDLR |= ((acc_enabled << 8) << 8) << 5;
    to_fwd->RDLR |= ((acc_decel_cmd << 8) << 8) << 8;

    to_fwd->RDHR |= command_type << 4;
    to_fwd->RDHR |= ((acc_brk_prep << 8) << 8) << 1;

    crc = fca_compute_checksum(to_fwd);
    to_fwd->RDHR |= (((crc << 8) << 8) << 8);   //replace Checksum
  }
  else { //pass through
    to_fwd->RDLR |= 0x00000000;
    to_fwd->RDHR |= 0x00000000;
  }
}

static void send_acc_dash_msg(CAN_FIFOMailBox_TypeDef *to_fwd){

  if (is_oplong_enabled && !org_collision_active) {
    to_fwd->RDLR &= 0x7C000000;
    to_fwd->RDHR &= 0x00C8C000;
    to_fwd->RDLR |= acc_text_msg;
    to_fwd->RDLR |= acc_set_speed_kph << 8;
    to_fwd->RDLR |= (acc_set_speed_mph << 8) << 8;
    to_fwd->RDLR |= (((acc_text_req << 8) << 8) << 8) << 7;

    to_fwd->RDHR |= cruise_state << 4;
    to_fwd->RDHR |= cruise_icon << 8;
    to_fwd->RDHR |= ((lead_dist << 8) << 8) << 8;
  }
  else { //pass through
    to_fwd->RDLR |= 0x00000000;
    to_fwd->RDHR |= 0x00000000;
  }
}

static void send_acc_accel_msg(CAN_FIFOMailBox_TypeDef *to_fwd){
  int crc;

  if (is_oplong_enabled && !org_collision_active) {
    to_fwd->RDHR &= 0x00FF0000; // keep the counter
    to_fwd->RDHR |= (acc_eng_req << 7);
    to_fwd->RDHR |= (acc_torq >> 8) | ((acc_torq << 8) & 0xFFFF);
    crc = fca_compute_checksum(to_fwd);
    to_fwd->RDHR |= (((crc << 8) << 8) << 8);   //replace Checksum
  }
  else { //pass through
    to_fwd->RDLR |= 0x00000000;
    to_fwd->RDHR |= 0x00000000;
  }
}

static void send_wheel_button_msg(CAN_FIFOMailBox_TypeDef *to_fwd){
  int crc;
  if (is_oplong_enabled) {
    to_fwd->RDLR &= 0x00F000; // keep the counter
    if (org_acc_available) {
        to_fwd->RDLR |= 0x80; // send acc button to remove acc available status
    }
  crc = fca_compute_checksum(to_fwd);
  to_fwd->RDLR |= ((crc << 8) << 8);   //replace Checksum
  }
  else { //pass through
    to_fwd->RDLR |= 0x00000000;
    to_fwd->RDHR |= 0x00000000;
  }
}

void chrysler_wp(void) {
  CAN1->sTxMailBox[0].TDLR = 0x00;
  CAN1->sTxMailBox[0].TDTR = 4;
  CAN1->sTxMailBox[0].TIR = (0x4FFU << 21) | 1U;
}

int default_rx_hook(CAN_FIFOMailBox_TypeDef *to_push) {
  int addr = GET_ADDR(to_push);
  int bus_num = GET_BUS(to_push);

  if ((addr == 658) && (bus_num == 0)) {
    is_op_active = (GET_BYTE(to_push, 0) >> 4) & 0x1;
    if (is_op_active) {
      steer_type = 1;
    } else {
      steer_type = 3;
    }
    lkas_torq = ((GET_BYTE(to_push, 0) & 0x7) << 8) | GET_BYTE(to_push, 1);
    counter_658 += 1;
  }

  if ((addr == 284) && (bus_num == 0)) {
    if (counter_502 > 0) {
        counter_284_502 += 1;
        if (counter_284_502 - counter_502 > 25) {
            is_oplong_enabled = false;
            acc_enabled = false;
            counter_502 = 0;
            counter_284_502 = 0;
        }
    }

    if (counter_658 > 0) {
        counter_284_658 += 2;
        if (counter_284_658 - counter_658 > 25){
            is_op_active = false;
            steer_type = 3;
            counter_658 = 0;
            counter_284_658 = 0;
        }
    }
  }

  if ((addr == 502) && (bus_num == 0)) {
    acc_stop = (GET_BYTE(to_push, 0) >> 5) & 0x1;
    acc_go = (GET_BYTE(to_push, 0) >> 6) & 0x1;
    acc_available = (GET_BYTE(to_push, 2) >> 4) & 0x1;
    acc_enabled = (GET_BYTE(to_push, 2) >> 5) & 0x1;
    acc_decel_cmd = ((GET_BYTE(to_push, 2) & 0xF) << 8) | GET_BYTE(to_push, 3);
    command_type = (GET_BYTE(to_push, 4) >> 4) & 0x7;
    acc_brk_prep = (GET_BYTE(to_push, 6) >> 1) & 0x1;
    counter_502 += 1;
  }

  if ((addr == 503) && (bus_num == 0)) {
    is_oplong_enabled = GET_BYTE(to_push, 3) & 0x1;
    acc_text_msg = GET_BYTE(to_push, 0);
    acc_set_speed_kph = GET_BYTE(to_push, 1);
    acc_set_speed_mph = GET_BYTE(to_push, 2);
    cruise_state = (GET_BYTE(to_push, 4) >> 4) & 0x7;
    cruise_icon = GET_BYTE(to_push, 5) & 0x3F;
    lead_dist = GET_BYTE(to_push, 7);
    acc_text_req = GET_BYTE(to_push, 3) >> 7;
  }

  if ((addr == 626) && (bus_num == 0)) {
    acc_eng_req = (GET_BYTE(to_push, 4) >> 7) & 0x1;
    acc_torq = (GET_BYTE(to_push, 4) & 0x7F) << 8 | GET_BYTE(to_push, 5);
  }

  if ((addr == 500) && (bus_num == 1)) {
    if (is_oplong_enabled) {
       org_acc_available = (GET_BYTE(to_push, 2) >> 4) & 0x1;
       org_cmd_type = (GET_BYTE(to_push, 4) >> 4) & 0x7;
       org_brk_pul = GET_BYTE(to_push, 6) & 0x1;
       if (org_brk_pul || (org_cmd_type > 1)) {
         org_collision_active = true;
       }
       else {
         org_collision_active = false;
       }
    }
    else{
       org_acc_available = false;
    }
  }
  return true;
}

// *** no output safety mode ***

static void nooutput_init(int16_t param) {
  UNUSED(param);
  controls_allowed = false;
  relay_malfunction_reset();
}

static int nooutput_tx_hook(CAN_FIFOMailBox_TypeDef *to_send) {
  UNUSED(to_send);
  return false;
}

static int nooutput_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  UNUSED(lin_num);
  UNUSED(data);
  UNUSED(len);
  return false;
}

static int default_fwd_hook(int bus_num, CAN_FIFOMailBox_TypeDef *to_fwd) {
  UNUSED(to_fwd);
  UNUSED(bus_num);

  return -1;
}

const safety_hooks nooutput_hooks = {
  .init = nooutput_init,
  .rx = default_rx_hook,
  .tx = nooutput_tx_hook,
  .tx_lin = nooutput_tx_lin_hook,
  .fwd = default_fwd_hook,
};

// *** all output safety mode ***

static void alloutput_init(int16_t param) {
  UNUSED(param);
  controls_allowed = true;
  relay_malfunction_reset();
}

static int alloutput_tx_hook(CAN_FIFOMailBox_TypeDef *to_send) {
  UNUSED(to_send);
  return true;
}

static int alloutput_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  UNUSED(lin_num);
  UNUSED(data);
  UNUSED(len);
  return true;
}

const safety_hooks alloutput_hooks = {
  .init = alloutput_init,
  .rx = default_rx_hook,
  .tx = alloutput_tx_hook,
  .tx_lin = alloutput_tx_lin_hook,
  .fwd = default_fwd_hook,
};
