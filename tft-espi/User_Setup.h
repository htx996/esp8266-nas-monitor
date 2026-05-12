// User_Setup.h for ESP8266 + ST7789 1.54 inch 240x240 TFT
// Wiring:
// SCK  -> GPIO14
// MOSI -> GPIO13
// DC   -> GPIO0
// RST  -> GPIO2
// BL   -> GPIO5, LOW = ON
// CS   -> GND, so TFT_CS = -1

#define USER_SETUP_INFO "ESP8266_ST7789_240x240_NAS_MONITOR"

#define ST7789_DRIVER

#define TFT_WIDTH  240
#define TFT_HEIGHT 240

// If red/blue are swapped, uncomment ONE option:
// #define TFT_RGB_ORDER TFT_RGB
// #define TFT_RGB_ORDER TFT_BGR

// If black/white are inverted, try ONE option:
// #define TFT_INVERSION_ON
// #define TFT_INVERSION_OFF

#define TFT_MOSI  13
#define TFT_SCLK  14

#define TFT_CS   -1
#define TFT_DC    0
#define TFT_RST   2

#define TFT_BL    5
#define TFT_BACKLIGHT_ON LOW

#define LOAD_GLCD
#define LOAD_FONT2
#define LOAD_FONT4
#define LOAD_FONT6
#define LOAD_FONT7
#define LOAD_FONT8
#define LOAD_GFXFF
#define SMOOTH_FONT

#define SPI_FREQUENCY  10000000
#define SPI_READ_FREQUENCY  10000000
#define SPI_TOUCH_FREQUENCY  2500000
