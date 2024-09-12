import pandas as pd

def leer_archivo_csv_o_txt(ruta_archivo):
    """
    Función para leer un archivo CSV o TXT y exportar la primera sección en formato separado por ';'.
    El archivo puede tener columnas con datos separados por tabulaciones o espacios múltiples.
    """

    try:
        with open(ruta_archivo, 'r') as file:
            # Leer la primera línea (cabecera)
            primera_fila = file.readline().rstrip()

            # Leer la segunda línea (número de frames)
            segunda_fila = file.readline().rstrip()
            num_frames = int(segunda_fila)
            print(f"Número de frames: {num_frames}")

            # Leer la tercera línea (atributos)
            atributos = file.readline().rstrip("\n")
            atributos_separados = atributos.split("\t")  # Mantener las tabulaciones originales

            # Leer la cuarta línea (nombres de columnas)
            columnas = file.readline().rstrip("\n").split("\t")

            # Leer la quinta línea (unidades de medida)
            unidades = file.readline().rstrip("\n").split("\t")

            # Definir una lista de nuevas columnas que quieras agregar
            nuevas_columnas = ["Tiempo"]  # Se puede expandir a más columnas
    
            # Función para agregar nuevas columnas en la posición deseada
            def agregar_columnas(fila, nuevas_columnas, posicion):
                for nueva_columna in nuevas_columnas:
                    fila.insert(posicion, nueva_columna)
                return fila

            # Ajuste general para cualquier fila (atributos, nombres de columnas, unidades, etc.)
            # Mantener las tabulaciones y espacios en blanco, pero unificar la lógica
            def ajustar_fila(lista):
                fila_final = []
                for item in lista:
                    if item.strip():  # Si el valor no está vacío
                        fila_final.append(item)
                    else:
                        fila_final.append('')  # Mantener la separación (espacios/tabulaciones en blanco)
                return ";".join(fila_final)
            
            # Agregar las nuevas columnas (vacías o con nombre) en la tercera posición
            atributos = agregar_columnas(atributos_separados, [""] * len(nuevas_columnas), 2)
            columnas = agregar_columnas(columnas, nuevas_columnas, 2)
            unidades = agregar_columnas(unidades, [""] * len(nuevas_columnas), 2)

            # Ajustar y convertir las filas leídas en cadenas separadas por ';'
            atributos_str = ajustar_fila(atributos_separados)
            columnas_str = ajustar_fila(columnas)
            unidades_str = ajustar_fila(unidades)

            # Exportar las primeras 5 filas en formato separado por ";"
            with open("estudios/test1.txt", 'w') as output_file:
                output_file.write(f"{primera_fila}\n{segunda_fila}\n{atributos_str}\n{columnas_str}\n{unidades_str}\n")
    
            # Leer las filas de mediciones a partir de la fila 6 y agregar la nueva columna "Tiempo"
            mediciones = []
            tiempo_anterior = 0  # Inicializar el tiempo
            for i, line in enumerate(file):
                if line.strip():  # Si la línea no está vacía
                    columnas_medicion = line.strip().replace("\t", ";").split(";")
                    if i == 0:
                        tiempo_actual = 0  # La primera fila siempre es 0
                    else:
                        tiempo_actual = tiempo_anterior + (1 / num_frames)

                    # Insertar la nueva columna "Tiempo" en la tercera posición
                    columnas_medicion.insert(2, f"{tiempo_actual:.6f}")
                    tiempo_anterior = tiempo_actual  # Actualizar el tiempo anterior

                    # Volver a juntar las columnas con ";"
                    mediciones.append(";".join(columnas_medicion))
                else:
                    break  # Detener la lectura cuando se encuentra una fila vacía

            # Escribir las mediciones al archivo, junto con la nueva columna de tiempo
            with open("estudios/test1.txt", 'a') as output_file:  # Modo 'a' para añadir al archivo existente
                for medicion in mediciones:
                    output_file.write(f"{medicion}\n")

            print("Primera sección exportada correctamente en 'estudios/test1.txt'.")

            return True

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
