import os
import pandas as pd
import numpy as np
from pathlib import Path
from tkinter import messagebox
# Usar importación relativa dentro del mismo paquete
from . import directory_manager, processors
from ..exceptions import ( # Importar excepciones desde el nivel superior (core)
    FileHandlerError,
    FileNotFoundError,
    InvalidFileFormatError,                                                                                                                                    
    IOError                                                                                                                                                    
)

def _determinar_frecuencia_por_contenido(linea_descripcion: str, linea_atributos: str) -> str:
    """Determina el tipo de frecuencia basado en palabras clave en las cabeceras."""
    # Priorizar "Model Outputs" ya que podría haber "Force Plate" en la descripción de cinemática
    if "Model Outputs" in linea_descripcion:
        return "Cinematica"
    elif "Force Plate" in linea_atributos: # Buscar en la línea de atributos/columnas
        return "Cinetica"
    # TODO: Añadir lógica para Electromiografica (ej. buscar "Delsys"?)
    # elif "Delsys" in linea_descripcion or "Delsys" in linea_atributos:
    #     return "Electromiografica"
    else:
        return "Desconocida"


def leer_seccion(file, num_frames: int, linea_descripcion: str, ruta_archivo_base: Path) -> tuple[list, list, str]:
    """
    Lee una sección del archivo, determina su tipo de frecuencia por contenido,
    y exporta el resultado a la ruta apropiada.

    :param file: Handle del archivo de entrada, posicionado al inicio de la sección (después de num_frames).
    :param num_frames: Número de frames de datos en la sección.
    :param linea_descripcion: La primera línea leída de la sección (puede contener "Model Outputs").
    :param ruta_archivo_base: Ruta base para guardar el archivo procesado (sin el sufijo de frecuencia).
    :return: Tupla (mediciones, columnas, tipo_frecuencia_determinado).
    """
    # Leer atributos, columnas, unidades (las siguientes 3 líneas)
    atributos_line = file.readline().rstrip("\n")
    columnas_line = file.readline().rstrip("\n")
    unidades_line = file.readline().rstrip("\n")

    atributos = atributos_line.split("\t")
    columnas = columnas_line.split("\t")
    unidades = unidades_line.split("\t")

    # Determinar tipo de frecuencia basado en el contenido de las cabeceras
    tipo_frecuencia = _determinar_frecuencia_por_contenido(linea_descripcion, atributos_line)

    # Construir la ruta final del archivo procesado con la frecuencia determinada
    nombre_archivo_procesado = ruta_archivo_base.name.replace(".txt", f"_{tipo_frecuencia}.txt").replace(".csv", f"_{tipo_frecuencia}.csv")
    ruta_archivo_seccion = ruta_archivo_base.parent / tipo_frecuencia / nombre_archivo_procesado
    # Asegurar que el directorio de frecuencia exista
    ruta_archivo_seccion.parent.mkdir(parents=True, exist_ok=True)

    # --- Determinar número esperado de columnas basado en la cabecera original ---
    num_original_header_cols = len(columnas) # Longitud después de split('\t')
    num_final_expected_cols = num_original_header_cols + 1 # +1 por Tiempo
    # Ya no leemos la primera línea de datos aquí para determinar columnas. Confiamos en la cabecera.

    # --- Preparar y ajustar cabeceras ---
    # Agregar la columna "Tiempo" a las listas de cabecera (índice 2)
    nuevas_columnas_tiempo = ["Tiempo"]
    atributos = processors.agregar_columnas(atributos, [""], 2) # "" para atributo Tiempo
    columnas = processors.agregar_columnas(columnas, nuevas_columnas_tiempo, 2)
    unidades = processors.agregar_columnas(unidades, [""], 2) # "" para unidad Tiempo

    # Función helper para ajustar longitud de lista
    def adjust_list_length(lst, target_len, default_val=""):
        current_len = len(lst)
        if current_len > target_len:
            return lst[:target_len]
        elif current_len < target_len:
            return lst + [default_val] * (target_len - current_len)
        return lst

    # Ajustar longitud de las cabeceras al número final esperado de columnas
    atributos = adjust_list_length(atributos, num_final_expected_cols)
    columnas = adjust_list_length(columnas, num_final_expected_cols)
    unidades = adjust_list_length(unidades, num_final_expected_cols)

    # Unir cabeceras ajustadas con ';'
    atributos_str = ";".join(atributos)
    columnas_str = ";".join(columnas)
    unidades_str = ";".join(unidades)

    # --- Leer las mediciones ---
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
    # Escribir la sección al archivo con separador ';' para TODO
    with open(ruta_archivo_seccion, 'w', encoding='utf-8') as output_file:
        # Escribir SOLO num_frames (línea 0), omitiendo linea_descripcion
        output_file.write(f"{num_frames}\n")
        # Escribir las líneas de atributos, columnas y unidades MODIFICADAS (con Tiempo y ';')
        # Estas serán ahora las líneas 1, 2 y 3 del archivo.
        output_file.write(f"{atributos_str}\n")
        output_file.write(f"{columnas_str}\n")
        output_file.write(f"{unidades_str}\n")
        # Escribir datos con formato y separador ';'
        for medicion in mediciones:
            output_file.write(";".join(processors.formato_personalizado(x) for x in medicion) + "\n")

    # Devolver también el tipo de frecuencia determinado
    return mediciones, columnas, tipo_frecuencia

def obtener_nombre_paciente(nombre_archivo: str) -> str:
    """Extrae el identificador del paciente del nombre del archivo."""
    # Asume que el identificador es la primera parte antes del primer espacio
    return nombre_archivo.split(" ")[0]

# La lógica de leer_archivo_csv_o_txt se ha movido a FileService._process_and_copy_file
# o se infiere directamente en _process_and_copy_file.
# Esta función ya no es necesaria aquí.

# La función obtener_nombre_paciente también se movió/integró en FileService.
