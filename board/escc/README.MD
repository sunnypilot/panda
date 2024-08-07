## Documentation
[see more](https://github.com/sunnypilot/sunnypilot/blob/5d754169a6285e88e755ff9a592a851cb92b0abc/docs/escc/ESCC%20IONIQ%20PHEV%20Guide.md)

### Detailed Connection List

#### Molex 5018762640 Pinout:

- Pin 1: GND
- Pin 2: IGN
- Pin 3: internal 120 Ohm Resistor, simply bridge to Pin 5
- Pin 4: C-CAN HIGH
- Pin 5: internal 120 Ohm Resistor, simply bridge to Pin 3
- Pin 6: C-CAN LOW
- Pin 8: L-CAN HIGH
- Pin 10: L-CAN LOW
- Pin 12: 12v
- Pin 14: 12v
- Pin 16: IGN
- Pin 18: L-CAN HIGH
- Pin 20: L-CAN LOW
- Pin 22: C-CAN HIGH
- Pin 24: C-CAN LOW
- Pin 26: GND

#### **IONIQ 2203663 (Car Harness, Female):**

- Pin 1: 12v -> Molex Pin 12
- Pin 4: GND -> Molex Pin 1
- Pin 7: C-CAN LOW -> Molex Pin 6
- Pin 8: C-CAN HIGH -> Molex Pin 4
- Pin 9: L-CAN LOW -> Molex Pin 10
- Pin 10: IGPM (IGN) -> Molex Pin 2
- Pin 18: L-CAN HIGH -> Molex Pin 8

#### **IONIQ 2203663 (Car Radar, Male):**

- Molex Pin: 14 -> Pin 1: 12v
- Molex Pin: 26 -> Pin 4: GND
- Molex Pin: 24 -> Pin 7: C-CAN LOW
- Molex Pin: 22 -> Pin 8: C-CAN HIGH
- Molex Pin: 20 -> Pin 9: L-CAN LOW
- Molex Pin: 16 -> Pin 10: IGN
- Molex Pin: 18 -> Pin 18: L-CAN HIGH


```
IONIQ 2203663               Molex 5018762640         IONIQ 2203663 
Car Harness (Female)                                 Car Radar (Male)
+-----+-----+               +-----+-----+            +-----+-----+
| 18  |  9  |               |  2  |  1  |            | 10  |  1  |
| 17  |  8  |               |  4  |  3  |            | 11  |  2  |
| 16  |  7  |               |  6  |  5  |            | 12  |  3  |
| 15  |  6  |               |  8  |  7  |            | 13  |  4  |
| 14  |  5  | NOTCH         | 10  |  9  |            | 14  |  5  | NOTCH
| 13  |  4  |               | 12  | 11  |            | 15  |  6  |
| 12  |  3  |               | 14  | 13  | NOTCH      | 16  |  7  |
| 11  |  2  |               | 16  | 15  |            | 17  |  8  |
| 10  |  1  |               | 18  | 17  |            | 18  |  9  |
+-----+-----+               | 20  | 19  |            +-----+-----+
                            | 22  | 21  |
                            | 24  | 23  |
                            | 26  | 25  |
                            +-----+-----+           

Connections:
Molex Pin 3 (120 Ohm)    <-->  Molex Pin 5  (120 Ohm)
Harness Pin 1  (12V)     <--> Molex Pin 12 (12V)
Harness Pin 4  (GND)     <--> Molex Pin 1  (GND)
Harness Pin 10 (IGN)     <--> Molex Pin 2  (IGN)            
Harness Pin 8  (C-CAN H) <--> Molex Pin 4  (C-CAN H)
Harness Pin 7  (C-CAN L) <--> Molex Pin 6  (C-CAN L)
Harness Pin 18 (L-CAN H) <--> Molex Pin 8  (L-CAN H)
Harness Pin 9  (L-CAN L) <--> Molex Pin 10 (L-CAN L)
                              Molex Pin 20 (L-CAN L) <-->  Radar Pin 9  (L-CAN L)
                              Molex Pin 18 (L-CAN H) <-->  Radar Pin 18 (L-CAN H)
                              Molex Pin 24 (C-CAN L) <-->  Radar Pin 7  (C-CAN L)
                              Molex Pin 22 (C-CAN H) <-->  Radar Pin 8  (C-CAN H)
                              Molex Pin 16 (IGN)     <-->  Radar Pin 10 (IGN)
                              Molex Pin 14 (12V)     <-->  Radar Pin 1  (12V)
                              Molex Pin 26 (GND)     <-->  Radar Pin 4  (GND)
```