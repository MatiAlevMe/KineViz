import os
import pandas as pd
import numpy as np

def formato_personalizado(valor):
    if isinstance(valor, float):
        if valor == 0:
            return "0"
        else:
            return f"{valor:.6f}".rstrip('0').rstrip('.')
    return str(valor)

def agregar_columnas(fila, nuevas_columnas, posicion):
    for nueva_columna in nuevas_columnas:
        fila.insert(posicion, nueva_columna)
    return fila

def ajustar_fila(lista):
    fila_final = []
    for item in lista:
        if item.strip():
            fila_final.append(item)
        else:
            fila_final.append('')  
    return ";".join(fila_final)

def leer_seccion(file, num_frames, ruta_archivo):
    """
    Lee una sección del archivo desde los atributos hasta los valores de medición,
    exportando el resultado a la ruta especificada.
    """
    # Leer atributos, columnas, unidades
    atributos = file.readline().rstrip("\n").split("\t")
    columnas = file.readline().rstrip("\n").split("\t")
    unidades = file.readline().rstrip("\n").split("\t")

    # Agregar la columna "Tiempo"
    nuevas_columnas = ["Tiempo"]
    atributos = agregar_columnas(atributos, [""] * len(nuevas_columnas), 2)
    columnas = agregar_columnas(columnas, nuevas_columnas, 2)
    unidades = agregar_columnas(unidades, [""] * len(nuevas_columnas), 2)

    # Ajustar filas
    atributos_str = ajustar_fila(atributos)
    columnas_str = ajustar_fila(columnas)
    unidades_str = ajustar_fila(unidades)

    # Leer las mediciones
    mediciones = []
    tiempo_anterior = 0
    #num_columnas = len(columnas) 

    for i, line in enumerate(file):
        if line.rstrip("\n"):  # Conserva las tabulaciones pero elimina el salto de línea
            columnas_medicion = line.rstrip("\n").split("\t")  # Dividir correctamente por tabulaciones
            
            #print("columnas",columnas_medicion)
            
            # Añadir la columna de tiempo en el lugar correcto
            if i == 0:
                tiempo_actual = 0
            else:
                tiempo_actual = tiempo_anterior + (1 / num_frames)
            columnas_medicion.insert(2, f"{tiempo_actual:.6f}")
            tiempo_anterior = tiempo_actual

            # Convertir los valores en flotantes si no están vacíos, de lo contrario, usar NaN
            mediciones.append([float(val) if val.strip() != '' else np.nan for val in columnas_medicion])

        else:
            break  # Si hay una línea vacía, salir del bucle

    # Verificar la longitud de las columnas y mediciones
    #print(f"Longitud de columnas: {num_columnas}")
    #print(f"Longitud de mediciones (primera fila): {len(mediciones[0]) if mediciones else 'Sin mediciones'}")

    # Escribir la sección al archivo
    with open(ruta_archivo, 'w') as output_file:
        output_file.write(f"{num_frames}\n{atributos_str}\n{columnas_str}\n{unidades_str}\n")
        for medicion in mediciones:
            output_file.write(";".join(formato_personalizado(x) for x in medicion) + "\n")
    
    return mediciones, columnas

def calcular_max_min_rango(df, columnas):
    # No es necesario rellenar NaN, Pandas maneja NaN en cálculos
    # Calcular máximos, mínimos y rangos, ignorando los NaN
    maximos = [''] * 2 + [df[col].max(skipna=True) for col in columnas[3:]]
    minimos = [''] * 2 + [df[col].min(skipna=True) for col in columnas[3:]]
    rangos = [''] * 2 + [(df[col].max(skipna=True) - df[col].min(skipna=True)) for col in columnas[3:]]
    return maximos, minimos, rangos

def exportar_calculos(output_file, maximos, minimos, rangos):
    output_file.write(f";;MAXIMO;{';'.join(map(str, maximos[2:]))}\n")
    output_file.write(f";;MINIMO;{';'.join(map(str, minimos[2:]))}\n")
    output_file.write(f";;RANGO;{';'.join(map(str, rangos[2:]))}\n")

def leer_archivo_csv_o_txt(ruta_archivo, nombre_estudio):
    """
    Lee el archivo completo, detectando todas las secciones y exportando cada una en su
    carpeta correspondiente según la frecuencia de medición.
    """
    try:
        ruta_estudio = os.path.join("estudios", nombre_estudio)
        os.makedirs(ruta_estudio, exist_ok=True)

        with open(ruta_archivo, 'r') as file:
            while True:
                primera_fila = file.readline().rstrip()
                if not primera_fila:  # EOF
                    break

                segunda_fila = file.readline().rstrip()
                if not segunda_fila.isdigit():
                    break
                num_frames = int(segunda_fila)

                if 100 <= num_frames <= 200:
                    tipo_frecuencia = "Cinemática"
                elif num_frames == 1000:
                    tipo_frecuencia = "Cinética"
                elif num_frames == 2000:
                    tipo_frecuencia = "Electromiográfica"
                else:
                    tipo_frecuencia = "Desconocida"

                carpeta_frecuencia = os.path.join(ruta_estudio, tipo_frecuencia)
                os.makedirs(carpeta_frecuencia, exist_ok=True)

                nombre_archivo = os.path.basename(ruta_archivo).replace(".txt", f"_{tipo_frecuencia}.txt")
                ruta_archivo_seccion = os.path.join(carpeta_frecuencia, nombre_archivo)

                # Leer y exportar la sección
                mediciones, columnas = leer_seccion(file, num_frames, ruta_archivo_seccion)

                # Convertir mediciones a DataFrame para calcular max/min/rango
                df = pd.DataFrame(mediciones, columns=columnas)

                maximos, minimos, rangos = calcular_max_min_rango(df, columnas)

                # Exportar cálculos de Maximo, Minimo y Rango al archivo
                with open(ruta_archivo_seccion, 'a') as output_file:
                    exportar_calculos(output_file, maximos, minimos, rangos)

    except Exception as e:
        print(f"Error al leer el archivo: {e}")