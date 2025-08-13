import serial               # Comunicación serial con Arduino
import time                 # Funciones de tiempo y pausas
import collections          # Para usar deque (cola con tamaño máximo)
import matplotlib.pyplot as plt    # Para graficar
import matplotlib.animation as animation  # Animaciones de gráficas
from matplotlib.lines import Line2D  # Para manejar líneas en las gráficas
from matplotlib.widgets import Button  # Botón interactivo en la interfaz
import numpy as np          # Operaciones numéricas (no usado explícitamente aquí)
import matplotlib.gridspec as gridspec  # Layout avanzado para figuras

# Configuración del puerto serial y parámetros generales
serialPort = "COM10"   # Puerto serial a usar (cambiar si es necesario)
baudRate = 9600        # Velocidad de comunicación
Samples = 50           # Número de muestras para mostrar en la gráfica
sampleTime = 200       # Tiempo entre muestras en ms
numData = 4            # Número de variables que esperamos recibir por serial

# Umbral para detectar presión alta y mostrar alerta
UMBRAL_PRESION_ALTA = 1015.0

# Límites mínimos y máximos para el eje Y de cada gráfica
ymin = [0, 0, 900, 0]
ymax = [1023, 50, 1100, 1000]

# Intento de conexión serial con Arduino
try:
    serialConnection = serial.Serial(serialPort, baudRate, timeout=1)
    time.sleep(2)              # Esperar que el puerto se estabilice
    serialConnection.flushInput()  # Limpiar buffer de entrada serial
    print(f"✅ Conectado a {serialPort}")
except:
    print("❌ No se pudo conectar al puerto.")
    exit()                    # Termina programa si no conecta

lines = []       # Lista para guardar objetos Line2D de las gráficas
data = []        # Lista para guardar datos recibidos (colas)
colors = ['blue', 'orange', 'green', 'purple']  # Colores para las líneas

# Inicializamos estructuras para almacenar datos y líneas gráficas
for i in range(numData):
    data.append(collections.deque(maxlen=Samples))  # Cola con máximo Samples elementos
    lines.append(Line2D([], [], color=colors[i]))   # Línea vacía para graficar

# Crear figura con layout GridSpec para posicionar gráficas y botón
fig = plt.figure(figsize=(10, 6))

# Definimos un layout 2 filas x 3 columnas, donde la última columna será para el botón
gs = gridspec.GridSpec(2, 3, width_ratios=[4, 4, 1], figure=fig, wspace=0.4)

# Crear subplots para las 4 gráficas en las primeras dos columnas
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 0])
ax4 = fig.add_subplot(gs[1, 1])

# Crear un "eje" especial para el botón en la columna derecha, ocupando ambas filas
ax_button = fig.add_subplot(gs[:, 2])
ax_button.axis('off')  # Ocultar ejes del área del botón

# Crear botón guardado de datos en la posición definida
btn_ax = fig.add_axes([0.85, 0.4, 0.1, 0.1])  # Coordenadas relativas para botón
btn_save = Button(btn_ax, 'Guardar datos')

# Configuración de límites, títulos y etiquetas para cada gráfica

# Gráfica MQ135 (valor crudo)
ax1.set_xlim(0, Samples)
ax1.set_ylim(ymin[0], ymax[0])
ax1.set_title("MQ135 (ppm)")
ax1.set_ylabel("Valor crudo")
ax1.add_line(lines[0])  # Añadir línea vacía para luego actualizar

# Gráfica temperatura
ax2.set_xlim(0, Samples)
ax2.set_ylim(ymin[1], ymax[1])
ax2.set_title("Temperatura (°C)")
ax2.set_ylabel("°C")
ax2.add_line(lines[1])

# Gráfica presión
ax3.set_xlim(0, Samples)
ax3.set_ylim(ymin[2], ymax[2])
ax3.set_title("Presión (hPa)")
ax3.set_ylabel("hPa")
ax3.add_line(lines[2])
ax3.axhline(UMBRAL_PRESION_ALTA, color='red', linestyle='--', linewidth=1, label="Presión Alta")  # Línea umbral
ax3.legend(loc='upper right')  # Mostrar leyenda

# Gráfica luz (lux)
ax4.set_xlim(0, Samples)
ax4.set_ylim(ymin[3], ymax[3])
ax4.set_title("Luz (Lux)")
ax4.set_ylabel("Lux")
ax4.add_line(lines[3])

# Función para guardar los datos en un archivo CSV cuando se presiona el botón
def save_data(event):
    filename = "datos_sensores.csv"
    try:
        with open(filename, 'w') as f:
            f.write("MQ135(Ppm),Temperatura(C),Presion(hPa),Luz(Lux)\n")  # Encabezado CSV
            max_len = min(len(d) for d in data)  # Número de datos mínimo para no indexar fuera de rango
            for i in range(max_len):
                fila = []
                for sensor_data in data:
                    fila.append(str(sensor_data[i]))  # Convertir dato a texto
                f.write(','.join(fila) + '\n')  # Guardar fila separada por comas
        print(f"Datos guardados en {filename}")
    except Exception as e:
        print(f"Error guardando datos: {e}")

btn_save.on_clicked(save_data)  # Vincular función al evento de clic del botón

# Función que se llama en cada frame para leer datos y actualizar gráficas
def getSerialData(frame, Samples, numData, serialConnection, lines):
    try:
        line = serialConnection.readline().decode().strip()  # Leer línea serial y limpiar
        if not line or "MQ135" in line:  # Ignorar líneas vacías o encabezados
            return
        parts = line.split(',')  # Separar datos por coma
        if len(parts) != numData:  # Validar número correcto de datos
            return
        for i in range(numData):
            value = float(parts[i])  # Convertir valor a float
            if i == 3:  # Para luz (índice 3), limitar valor máximo a 850
                value = min(value, 850)
            data[i].append(value)  # Añadir dato a la cola
            ydata = list(data[i])
            xdata = list(range(len(ydata)))
            lines[i].set_data(xdata, ydata)  # Actualizar datos de la línea para graficar
        presion_actual = float(parts[2])  # Obtener valor de presión actual
        if presion_actual > UMBRAL_PRESION_ALTA:  # Detectar presión alta y mostrar alerta
            print(f"[!] Presión alta detectada: {presion_actual} hPa")
    except Exception as e:
        print("Error leyendo datos:", e)

# Crear animación que ejecuta getSerialData cada sampleTime milisegundos
anim = animation.FuncAnimation(
    fig, getSerialData,
    fargs=(Samples, numData, serialConnection, lines),
    interval=sampleTime,
    cache_frame_data=False
)

plt.show()               # Mostrar ventana gráfica
serialConnection.close() # Cerrar conexión serial al terminar
