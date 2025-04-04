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
    atributos = processors.agregar_columnas(atributos, [""] * len(nuevas_columnas), 2)
    columnas = processors.agregar_columnas(columnas, nuevas_columnas, 2)
    unidades = processors.agregar_columnas(unidades, [""] * len(nuevas_columnas), 2)

    # Ajustar filas
    atributos_str = processors.ajustar_fila(atributos)
    columnas_str = processors.ajustar_fila(columnas)
    unidades_str = processors.ajustar_fila(unidades)

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
            output_file.write(";".join(processors.formato_personalizado(x) for x in medicion) + "\n")
    return mediciones, columnas

def obtener_nombre_paciente(nombre_archivo: str) -> str:
    """Extrae el identificador del paciente del nombre del archivo."""
    # Asume que el identificador es la primera parte antes del primer espacio
    return nombre_archivo.split(" ")[0]

# La lógica de leer_archivo_csv_o_txt se ha movido a FileService._process_and_copy_file
# o se infiere directamente en _process_and_copy_file.
# Esta función ya no es necesaria aquí.

# La función obtener_nombre_paciente también se movió/integró en FileService.
