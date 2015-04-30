#include <RF24Network.h>
#include <RF24.h>
#include <SPI.h>
#include <Bounce2.h>

//#define DEBUG
#ifdef DEBUG
#include "printf.h"
#endif


#define THIS_NODE 01
#define PIN_PULSE 2
#define PIN_NTC   A0


// nrf24l01
RF24 radio(9,10);
RF24Network network(radio);
RF24NetworkHeader header(/*to node*/ 00, /*type*/ 'T' /*Time*/);

Bounce pulse_input;


//-----------------------------------------------------------------------------
inline int clamp(const int a, const int min, const int max)
{
  return a < min ? min : (a > max ? max : a);
}

//-----------------------------------------------------------------------------
// Convert ADC value from thermistor to floating point temperature
float getTempFromValue(int RawADC)
{
  long Resistance;
  float Temp;

  // Valid from 1 to 1023 (0 and 1024 both produce devide by zero!)
  //RawADC = clamp(RawADC, 1, 1023);

  // Assuming a 10k Thermistor.  Calculation is actually: Resistance = (1024/ADC)
  Resistance=((10240000/RawADC) - 10000);

  /******************************************************************/
  /* Utilizes the Steinhart-Hart Thermistor Equation:				*/
  /*    Temperature in Kelvin = 1 / {A + B[ln(R)] + C[ln(R)]^3}		*/
  /*    where A = 0.001129148, B = 0.000234125 and C = 8.76741E-08	*/
  /******************************************************************/
  Temp = log(Resistance);
  Temp = 1 / (0.001129148 + (0.000234125 * Temp) + (0.0000000876741 * Temp * Temp * Temp));
  Temp = Temp - 273.15;  // Convert Kelvin to Celsius

  return Temp;  // Return the Temperature
}

//------------------------------------------------------------------------------
void setup()
{
#ifdef DEBUG
  Serial.begin(115200);
  printf_begin();
  printf_P(PSTR("\n\rSensor Node\n\r"));
#endif

  // Setup nrf24l01
  SPI.begin();
  radio.begin();
  radio.setPALevel(RF24_PA_HIGH);
  network.begin(/*channel*/ 90, THIS_NODE);

  // Setup pulse input pin
  pinMode(PIN_PULSE, INPUT_PULLUP);
  pulse_input.attach(PIN_PULSE);
  pulse_input.interval(10); // interval in ms
}

//------------------------------------------------------------------------------
struct SUpdateMessage
{
  char name[4];
  uint32_t millis;
  uint32_t value;
};

//------------------------------------------------------------------------------
void _sendUpdate(uint32_t millis, char * name, void * value)
{
  SUpdateMessage msg;

  for(int i = 0; i < 4; i++) msg.name[i] = name[i];
  msg.millis = millis;
  msg.value = *((uint32_t *)value);

  network.write(header, &msg, sizeof(SUpdateMessage));
}

//------------------------------------------------------------------------------
void sendUpdate(uint32_t millis, char * name, uint32_t value)
{
#ifdef DEBUG
  printf_P(PSTR("sendUpdate(%lu, %c%c%c%c, %lu)\n"), millis, name[0], name[1], name[2], name[3], value);
#endif

  _sendUpdate(millis, name, &value);
}

//------------------------------------------------------------------------------
void sendUpdate(uint32_t millis, char * name, int32_t value)
{
#ifdef DEBUG
  printf_P(PSTR("sendUpdate(%lu, %c%c%c%c, %ld)\n"), millis, name[0], name[1], name[2], name[3], value);
#endif

  _sendUpdate(millis, name, &value);
}

//------------------------------------------------------------------------------
void sendUpdate(uint32_t millis, char * name, int value)
{
  sendUpdate(millis, name, (int32_t)value);
}

//------------------------------------------------------------------------------
void sendUpdate(uint32_t millis, char * name, float value)
{
#ifdef DEBUG
  printf_P(PSTR("sendUpdate(%lu, %c%c%c%c, %ld)\n"), millis, name[0], name[1], name[2], name[3], (int32_t)value);
#endif

  _sendUpdate(millis, name, &value);
}

//------------------------------------------------------------------------------
void loop()
{
  uint32_t iPulseCounter = 0;

  uint32_t tmLoop;
  uint32_t tmWatchdog = 0;

  while(true)
  {
    tmLoop = millis();

    // Watchdog
    if((tmLoop - tmWatchdog) > 10000)
    {
      tmWatchdog += 10000;
      
      float fTemp = getTempFromValue(analogRead(PIN_NTC));
      sendUpdate(tmLoop, "TMP0", (int32_t)fTemp);
    }

    // Pulse counter, update counter on falling edge of input
    if(pulse_input.update())
    {
      if(pulse_input.fell())
        sendUpdate(tmLoop, "CNT0", iPulseCounter++);
    }
  }
}
