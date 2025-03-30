import os
import pandas as pd
import numpy as np
from pathlib import Path
from tkinter import messagebox
 
from core.data_processing import directory_manager, processors
from core.exceptions import (                                                                                                                                  
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

def obtener_nombre_paciente(nombre_archivo):
    return nombre_archivo.split(" ")[0]

def leer_archivo_csv_o_txt(ruta_archivo: Path, nombre_estudio: str, nombre_paciente: str = None) -> str:
    """
    Lee el archivo completo, detectando todas las secciones y exportando cada una en su
    carpeta correspondiente según la frecuencia de medición.
    """
    try:
        if not ruta_archivo.exists():                                                                                                                          
            raise FileNotFoundError(ruta_archivo) 
        
        # Obtener nombre del paciente  
        if nombre_paciente is None:
            nombre_paciente = obtener_nombre_paciente(ruta_archivo.name)

        # 1. Crear estructura de directorios usando directory_manager   
        ruta_estudio = directory_manager.crear_estructura_estudio(nombre_estudio)
        ruta_paciente = directory_manager.crear_estructura_paciente(ruta_estudio, nombre_paciente)    

        # 2. Copiar archivo original a OG                                                                                                                      
        ruta_og = ruta_paciente / "OG"                                                                                                                         
        archivo_og = ruta_og / ruta_archivo.name                                                                                                               
        directory_manager.copiar_archivo_origen(ruta_archivo, archivo_og) 

        # 3. Procesar archivo
        with open(ruta_archivo, 'r') as file:
            while True:
                # Validar formato básico
                primera_fila = file.readline().rstrip()
                if not primera_fila:  # EOF
                    break
                
                # Leer número de frames
                segunda_fila = file.readline().rstrip()
                if not segunda_fila.isdigit():
                    raise InvalidFileFormatError("Falta número de frames válido")
                num_frames = int(segunda_fila)

                tipo_frecuencia = directory_manager.determinar_tipo_frecuencia(num_frames)

                carpeta_frecuencia = directory_manager.crear_carpeta_frecuencia(ruta_paciente, tipo_frecuencia)

                # Generar nombre de archivo procesado 
                nombre_archivo = ruta_archivo.name.replace(".txt", f"_{tipo_frecuencia}.txt")                                                                                  
                ruta_archivo_seccion = carpeta_frecuencia / nombre_archivo 

                # Procesar sección
                mediciones, columnas = leer_seccion(file, num_frames, ruta_archivo_seccion)

                # Cálculos estadísticos
                df = pd.DataFrame(mediciones, columns=columnas)
                df.columns = [f'{col}_{i}' if df.columns.duplicated()[i]
                              else col for i, col in enumerate(df.columns)]

                maximos, minimos, rangos = processors.calcular_max_min_rango(df, columnas)

                # Exportar resultados
                with open(ruta_archivo_seccion, 'a') as output_file:
                    processors.exportar_calculos(output_file, maximos, minimos, rangos)
        return nombre_paciente

    except FileNotFoundError as e:                                                                                                                             
        raise                                                                                                                                                  
    except IOError as e:                                                                                                                                       
        raise IOError(f"Error leyendo {ruta_archivo}") from e                                                                                                  
    except ValueError as e:                                                                                                                                    
        raise InvalidFileFormatError(str(e)) from e                                                                                                            
    except Exception as e:                                                                                                                                     
        raise FileHandlerError(f"Error inesperado: {str(e)}") from e    