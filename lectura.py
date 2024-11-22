"""
Funciones para leer y formatear archivos de texto.
"""
from genericpath import isfile
import os
import shutil
import pandas as pd
import numpy as np
from tkinter import messagebox

def formato_personalizado(valor):
    """
    Formatea un valor de medición para ser exportado a un archivo de texto.
    Si el valor es un número, lo formatea con 6 decimales.
    Si el valor es una cadena, lo formatea como una cadena.
    """
    if isinstance(valor, float):
        if valor == 0:
            return "0"
        else:
            return f"{valor:.6f}".rstrip('0').rstrip('.')
    return str(valor)

def agregar_columnas(fila, nuevas_columnas, posicion):
    """
    Agrega columnas a una fila de mediciones.
    """
    for nueva_columna in nuevas_columnas:
        fila.insert(posicion, nueva_columna)
    return fila

def ajustar_fila(lista):
    """
    Ajusta una fila de mediciones para que contenga el mismo número de columnas.
    Si una columna está vacía, la agrega con un valor vacío.
    """
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

    for i, line in enumerate(file):
        if line.rstrip("\n"):  # Conserva las tabulaciones pero elimina el salto de línea
            # Dividir correctamente por tabulaciones
            columnas_medicion = line.rstrip("\n").split("\t")
            # Añadir la columna de tiempo en el lugar correcto
            if i == 0:
                tiempo_actual = 0
            else:
                tiempo_actual = tiempo_anterior + (1 / num_frames)
            columnas_medicion.insert(2, f"{tiempo_actual:.6f}")
            tiempo_anterior = tiempo_actual

            # Convertir los valores en flotantes si no están vacíos, de lo contrario, usar NaN
            mediciones.append([float(val) if val.strip() !=
                               '' else np.nan for val in columnas_medicion])

        else:
            break  # Si hay una línea vacía, salir del bucle
    # Escribir la sección al archivo
    with open(ruta_archivo, 'w') as output_file:
        output_file.write(f"{num_frames}\n{atributos_str}\n{columnas_str}\n{unidades_str}\n")
        for medicion in mediciones:
            output_file.write(";".join(formato_personalizado(x) for x in medicion) + "\n")
    return mediciones, columnas

def calcular_max_min_rango(df, columnas):
    """
    Calcula maximos, minimos y rangos de mediciones en una DataFrame.
    Ignora NaN.
    """
    # No es necesario rellenar NaN, Pandas maneja NaN en cálculos
    # Calcular maximos, minimos y rangos, ignorando los NaN
    maximos = [''] * 2 + [df[col].max(skipna=True) for col in columnas[3:]]
    minimos = [''] * 2 + [df[col].min(skipna=True) for col in columnas[3:]]
    rangos = [''] * 2 + [(df[col].max(skipna=True) - df[col].min(skipna=True))
                         for col in columnas[3:]]
    return maximos, minimos, rangos

def exportar_calculos(output_file, maximos, minimos, rangos):
    """
    Exporta calculos de Maximo, Minimo y Rango a un archivo de texto.
    """
    output_file.write(f";;MAXIMO;{';'.join(map(str, maximos[2:]))}\n")
    output_file.write(f";;MINIMO;{';'.join(map(str, minimos[2:]))}\n")
    output_file.write(f";;RANGO;{';'.join(map(str, rangos[2:]))}\n")

def obtener_nombre_paciente(nombre_archivo):
    return nombre_archivo.split(" ")[0]

def leer_archivo_csv_o_txt(ruta_archivo, nombre_estudio, nombre_paciente=None):
    """
    Lee el archivo completo, detectando todas las secciones y exportando cada una en su
    carpeta correspondiente según la frecuencia de medición.
    """
    try:
        if nombre_paciente is None:
            nombre_paciente = obtener_nombre_paciente(os.path.basename(ruta_archivo))

        # Crear la estructura de directorios correcta
        ruta_estudio = os.path.join("estudios", nombre_estudio)
        os.makedirs(ruta_estudio, exist_ok=True)

        ruta_paciente = os.path.join(ruta_estudio, nombre_paciente)
        os.makedirs(ruta_paciente, exist_ok=True)

        # Crear la carpeta OG
        ruta_og = os.path.join(ruta_paciente, "OG")
        os.makedirs(ruta_og, exist_ok=True)

        # Copiar el archivo original a la carpeta OG
        nombre_archivo_og = os.path.basename(ruta_archivo)
        ruta_archivo_og = os.path.join(ruta_og, nombre_archivo_og)
        shutil.copy2(ruta_archivo, ruta_archivo_og)

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
                    tipo_frecuencia = "Cinematica"
                elif num_frames == 1000:
                    tipo_frecuencia = "Cinetica"
                elif num_frames == 2000:
                    tipo_frecuencia = "Electromiografica"
                else:
                    tipo_frecuencia = "Desconocida"

                carpeta_frecuencia = os.path.join(ruta_paciente, tipo_frecuencia)
                os.makedirs(carpeta_frecuencia, exist_ok=True)

                nombre_archivo = os.path.basename(ruta_archivo).replace(".txt",
                                                                        f"_{tipo_frecuencia}.txt")
                ruta_archivo_seccion = os.path.join(carpeta_frecuencia, nombre_archivo)

                # Leer y exportar la sección
                mediciones, columnas = leer_seccion(file, num_frames, ruta_archivo_seccion)

                # Convertir mediciones a DataFrame para calcular max/min/rango
                df = pd.DataFrame(mediciones, columns=columnas)
                df.columns = [f'{col}_{i}' if df.columns.duplicated()[i]
                              else col for i, col in enumerate(df.columns)]

                maximos, minimos, rangos = calcular_max_min_rango(df, columnas)

                # Exportar calculos de Maximo, Minimo y Rango al archivo
                with open(ruta_archivo_seccion, 'a') as output_file:
                    exportar_calculos(output_file, maximos, minimos, rangos)

    except FileNotFoundError:
        messagebox.showerror("Error", f"Error: El archivo {ruta_archivo} no se encontró.")
    except IOError as e:
        messagebox.showerror("Error", f"Error de entrada/salida al leer el archivo: {e}")
    except ValueError as e:
        messagebox.showerror("Error", f"Error: Formato de datos invalido en el archivo: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {e}")
    return nombre_paciente
