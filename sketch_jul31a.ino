#include <Wire.h>               // Librería para comunicación I2C
#include <BH1750.h>             // Librería para sensor de luz BH1750
#include <Adafruit_BMP085.h>    // Librería para sensor BMP180 (temperatura y presión)
#include <Adafruit_GFX.h>       // Librería gráfica base para pantalla OLED
#include <Adafruit_SSD1306.h>   // Librería para pantalla OLED SSD1306

// Definición de dimensiones para la pantalla OLED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1           // Pin de reset OLED no usado (-1)

// Creación de objetos para la pantalla, sensor de luz y sensor de presión/temperatura
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
BH1750 lightMeter;
Adafruit_BMP085 bmp;

const int mq135Pin = A0;        // Pin analógico para sensor MQ135 (calidad de aire)

// Función para dibujar ícono pequeño de nube (representa MQ135)
void drawMQ135IconSmall(int x, int y) {
  display.fillCircle(x + 3, y + 3, 3, SSD1306_WHITE);
  display.fillCircle(x + 7, y + 3, 3, SSD1306_WHITE);
  display.fillCircle(x + 5, y + 1, 4, SSD1306_WHITE);
  display.fillRect(x + 2, y + 5, 6, 3, SSD1306_WHITE);
}

// Función para dibujar ícono pequeño de termómetro (representa BMP180)
void drawBMP180IconSmall(int x, int y) {
  display.drawRect(x + 4, y, 4, 14, SSD1306_WHITE);
  display.fillRect(x + 5, y + 10, 2, 4, SSD1306_WHITE);
  display.drawCircle(x + 6, y + 18, 3, SSD1306_WHITE);
  display.fillCircle(x + 6, y + 18, 1, SSD1306_WHITE);
}

// Función para dibujar ícono pequeño de sol (representa BH1750)
void drawBH1750IconSmall(int x, int y) {
  display.drawCircle(x + 6, y + 6, 3, SSD1306_WHITE);
  // Dibuja los rayos del sol en 8 direcciones usando líneas
  for (int i = 0; i < 8; i++) {
    float angle = i * PI / 4;                // Ángulo en radianes (cada 45 grados)
    int x1 = x + 6 + cos(angle) * 4;         // Punto inicial del rayo
    int y1 = y + 6 + sin(angle) * 4;
    int x2 = x + 6 + cos(angle) * 6;         // Punto final del rayo
    int y2 = y + 6 + sin(angle) * 6;
    display.drawLine(x1, y1, x2, y2, SSD1306_WHITE);
  }
}

void setup() {
  Serial.begin(9600);         // Inicia comunicación serial a 9600 baudios
  Wire.begin();               // Inicia comunicación I2C
  delay(500);                 // Pequeña pausa para estabilizar

  // Inicializa pantalla OLED, con dirección I2C 0x3C
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("Error al iniciar OLED.");
    while (1);                // Si falla, queda en bucle infinito
  }

  display.clearDisplay();     // Limpia la pantalla OLED
  display.display();          // Actualiza la pantalla

  // Inicializa sensor de luz BH1750 en modo alta resolución continuo
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("BH1750 iniciado correctamente.");
  } else {
    Serial.println("Error: No se detecta el BH1750.");
    while (1);                // Si falla, queda en bucle infinito
  }

  // Inicializa sensor BMP180 (temperatura y presión)
  if (bmp.begin()) {
    Serial.println("BMP180 iniciado correctamente.");
  } else {
    Serial.println("Error: No se detecta el BMP180.");
    while (1);                // Si falla, queda en bucle infinito
  }

  Serial.println("MQ135 listo para lectura."); 
  // Imprime encabezado CSV para facilitar lectura de datos por software externo
  Serial.println("MQ135,BMP180_Temp,BMP180_Pres,BH1750_Lux");
}

void loop() {
  int mq135Val = analogRead(mq135Pin);       // Lee valor analógico del sensor MQ135
  float temp = bmp.readTemperature();        // Lee temperatura del BMP180
  float presion = bmp.readPressure() / 100.0;// Lee presión y la convierte a hPa
  float lux = lightMeter.readLightLevel();   // Lee nivel de luz del BH1750

  // Envia datos seriales separados por coma para que Python (u otro programa) los lea fácilmente
  Serial.print(mq135Val);
  Serial.print(",");
  Serial.print(temp, 2);
  Serial.print(",");
  Serial.print(presion, 2);
  Serial.print(",");
  Serial.println(lux, 2);

  // Convierte valores en rangos porcentuales para mostrar barras o indicadores visuales
  int mq135Pct = map(mq135Val, 0, 1023, 0, 100);
  int tempPct = map((int)temp, 0, 50, 0, 100);
  int presPct = map((int)presion, 900, 1100, 0, 100);
  int luxPct = map((int)lux, 0, 1000, 0, 100);

  // Limita los porcentajes a un rango válido (0 a 100)
  mq135Pct = constrain(mq135Pct, 0, 100);
  tempPct = constrain(tempPct, 0, 100);
  presPct = constrain(presPct, 0, 100);
  luxPct = constrain(luxPct, 0, 100);

  // Limpia pantalla antes de actualizar valores
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);    // Establece color del texto
  display.setTextSize(1);                  // Establece tamaño del texto

  // Muestra valor y porcentaje de MQ135 en la pantalla
  display.setCursor(0, 0);
  display.print("MQ135: ");
  display.print(mq135Val); 
  display.print(" (");
  display.print(mq135Pct);
  display.print("%)");
  drawMQ135IconSmall(115, 2);              // Dibuja ícono de MQ135 al lado derecho

  // Muestra temperatura y porcentaje
  display.setCursor(0, 16);
  display.print("Temp : ");
  display.print(temp, 1);
  display.print("C (");
  display.print(tempPct);
  display.print("%)");
  drawBMP180IconSmall(115, 17);            // Ícono termómetro al lado derecho

  // Muestra presión y porcentaje
  display.setCursor(0, 32);
  display.print("Pres : ");
  display.print(presion, 0);
  display.print("hPa (");
  display.print(presPct);
  display.print("%)");

  // Muestra nivel de luz y porcentaje
  display.setCursor(0, 48);
  display.print("Luz  : ");
  display.print((int)lux);
  display.print("Lx (");
  display.print(luxPct);
  display.print("%)");
  drawBH1750IconSmall(115, 45);            // Ícono sol al lado derecho

  display.display();                        // Actualiza pantalla con nuevos datos

  delay(200);  // Pausa breve para dar tiempo y mejorar fluidez de lectura en Python
}
