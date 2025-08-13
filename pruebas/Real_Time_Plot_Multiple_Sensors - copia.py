import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
from matplotlib.widgets import Button
import numpy as np
import matplotlib.gridspec as gridspec

# Configuración de puerto serial
serialPort = "COM10"# ⚠️ CAMBIA si es necesario"
baudRate = 9600
Samples = 50
sampleTime = 200  # ms
numData = 4

UMBRAL_PRESION_ALTA = 1015.0

ymin = [0, 0, 900, 0]
ymax = [1023, 50, 1100, 1000]

try:
    serialConnection = serial.Serial(serialPort, baudRate, timeout=1)
    time.sleep(2)
    serialConnection.flushInput()
    print(f"✅ Conectado a {serialPort}")
except:
    print("❌ No se pudo conectar al puerto.")
    exit()

lines = []
data = []
colors = ['blue', 'orange', 'green', 'purple']

for i in range(numData):
    data.append(collections.deque(maxlen=Samples))  # deque vacío, sin ceros iniciales
    lines.append(Line2D([], [], color=colors[i]))

# Usar GridSpec para layout: 2 columnas (gráficas y botón)
fig = plt.figure(figsize=(10, 6))
gs = gridspec.GridSpec(2, 2, width_ratios=[4, 1], figure=fig, wspace=0.3)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 0])
ax4 = fig.add_subplot(gs[1, 1])

# Configurar ejes para gráficas, colocamos el botón en un eje separado
# Redefinir el layout para las gráficas en una cuadrícula 2x2 (solo en la columna izquierda)
# El botón estará a la derecha en una columna más angosta.

# Sin embargo, para mantener los gráficos como antes y añadir el botón a la derecha:
# En lugar de usar 2x2, hacemos 2x1 y 1 columna más a la derecha para el botón

plt.clf()  # Limpiar figura porque vamos a redefinir con más control

gs = gridspec.GridSpec(2, 3, width_ratios=[4, 4, 1], figure=fig, wspace=0.4)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 0])
ax4 = fig.add_subplot(gs[1, 1])
ax_button = fig.add_subplot(gs[:, 2])  # botón ocupa toda la columna derecha

# Botón no puede ser un subplot normal, lo convertimos en axes para el botón
ax_button.axis('off')  # ocultamos ejes

btn_ax = fig.add_axes([0.85, 0.4, 0.1, 0.1])
btn_save = Button(btn_ax, 'Guardar datos')

# Configuramos los gráficos con límites y títulos
ax1.set_xlim(0, Samples)
ax1.set_ylim(ymin[0], ymax[0])
ax1.set_title("MQ135 (ppm)")
ax1.set_ylabel("Valor crudo")

ax1.add_line(lines[0])

ax2.set_xlim(0, Samples)
ax2.set_ylim(ymin[1], ymax[1])
ax2.set_title("Temperatura (°C)")
ax2.set_ylabel("°C")

ax2.add_line(lines[1])

ax3.set_xlim(0, Samples)
ax3.set_ylim(ymin[2], ymax[2])
ax3.set_title("Presión (hPa)")
ax3.set_ylabel("hPa")

ax3.add_line(lines[2])
ax3.axhline(UMBRAL_PRESION_ALTA, color='red', linestyle='--', linewidth=1, label="Presión Alta")
ax3.legend(loc='upper right')

ax4.set_xlim(0, Samples)
ax4.set_ylim(ymin[3], ymax[3])
ax4.set_title("Luz (Lux)")
ax4.set_ylabel("Lux")

ax4.add_line(lines[3])

def save_data(event):
    filename = "datos_sensores.csv"
    try:
        with open(filename, 'w') as f:
            f.write("MQ135(Ppm),Temperatura(C),Presion(hPa),Luz(Lux)\n")
            # Los datos podrían no tener aun Samples valores, así que tomamos min(len) de las colas
            max_len = min(len(d) for d in data)
            for i in range(max_len):
                fila = []
                for sensor_data in data:
                    fila.append(str(sensor_data[i]))
                f.write(','.join(fila) + '\n')
        print(f"Datos guardados en {filename}")
    except Exception as e:
        print(f"Error guardando datos: {e}")

btn_save.on_clicked(save_data)

def getSerialData(frame, Samples, numData, serialConnection, lines):
    try:
        line = serialConnection.readline().decode().strip()
        if not line or "MQ135" in line:
            return
        parts = line.split(',')
        if len(parts) != numData:
            return
        for i in range(numData):
            value = float(parts[i])
            if i == 3:  # Lux limitado a 800
                value = min(value, 850)
            data[i].append(value)
            # Para graficar, si no hay suficientes datos, graficamos solo lo que hay
            ydata = list(data[i])
            xdata = list(range(len(ydata)))
            lines[i].set_data(xdata, ydata)
        presion_actual = float(parts[2])
        if presion_actual > UMBRAL_PRESION_ALTA:
            print(f"[!] Presión alta detectada: {presion_actual} hPa")
    except Exception as e:
        print("Error leyendo datos:", e)

anim = animation.FuncAnimation(
    fig, getSerialData,
    fargs=(Samples, numData, serialConnection, lines),
    interval=sampleTime,
    cache_frame_data=False
)


plt.show()
serialConnection.close()