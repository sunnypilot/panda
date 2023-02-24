void smdps_clu11(void);

static void send_mdps_enable_speed(CAN_FIFOMailBox_TypeDef *to_fwd){
  bool is_speed_unit_mph = GET_BYTE(to_fwd, 2) & 0x2;
  
  int mdps_cutoff_speed = is_speed_unit_mph ? 76 : 120;  // factor of 2 from dbc
  
  int veh_clu_speed = GET_BYTE(to_fwd, 1) | (GET_BYTE(to_fwd, 2) & 0x1) << 8;
  
  if (veh_clu_speed < mdps_cutoff_speed) {
    to_fwd->RDLR &= 0xFFFE00FF;
    to_fwd->RDLR |= mdps_cutoff_speed << 8;
  }
};

int default_rx_hook(CAN_FIFOMailBox_TypeDef *to_push) {
  UNUSED(to_push);
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
  int addr = GET_ADDR(to_fwd);
  int bus_fwd = -1;
  
  if (bus_num == 0) {
    bus_fwd = 2;
   // if (addr == 1265) {
    //  send_mdps_enable_speed(to_fwd);
    //}
    //smdps_clu11();
  }
  if (bus_num == 2) {
    bus_fwd = 0;
  }
  return bus_fwd;
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
