#include <Encoder.h>

#define ENCODER_CLK 2
#define ENCODER_DT 3
#define ENCODER_SW 4  // Botón del encoder

Encoder encoder(ENCODER_CLK, ENCODER_DT);

long oldPosition = -999;
int baseValue = 0;

void setup() {
  Serial.begin(9600);
  pinMode(ENCODER_SW, INPUT_PULLUP);  // Botón con pull-up
  delay(1000);
  Serial.println("MQ135,BMP180_Temp,BMP180_Pres,BH1750_Lux");
}

void loop() {
  bool botonPresionado = digitalRead(ENCODER_SW) == LOW;

  long newPosition = encoder.read();

  // Limitar el valor base entre 0 y 1023
  if (newPosition < 0) {
    encoder.write(0);
    baseValue = 0;
  } else if (newPosition > 1023) {
    encoder.write(1023);
    baseValue = 1023;
  } else {
    baseValue = newPosition;
  }

  int mq135Val;
  float temp;
  float presion;
  float lux;

  if (botonPresionado) {
    // Valores máximos si el botón está presionado
    mq135Val = 1023;
    temp = 50.0;
    presion = 1100.0;
    lux = 1000.0;
  } else {
    // Valores basados en la rotación del encoder
    mq135Val = baseValue;
    temp = map(baseValue, 0, 1023, 0, 50);
    presion = map(baseValue, 0, 1023, 900, 1100);
    lux = map(baseValue, 0, 1023, 0, 1000);
  }

  Serial.print(mq135Val);
  Serial.print(",");
  Serial.print(temp, 2);
  Serial.print(",");
  Serial.print(presion, 2);
  Serial.print(",");
  Serial.println(lux, 2);

  delay(200);
}
