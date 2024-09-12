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

          # Leer las mediciones a partir de la fila 6 y calcular la nueva columna "Tiempo"
            mediciones = []
            tiempo_actual = 0.0
            delta_tiempo = 1 / num_frames

            for line in file:
                if line.strip():
                    columnas_medicion = line.strip().split("\t")
                    columnas_medicion.insert(2, f"{round(tiempo_actual, 2)}")  # Añadir la columna de tiempo redondeada
                    mediciones.append([float(val) if i > 1 else val for i, val in enumerate(columnas_medicion)])
                    tiempo_actual += delta_tiempo
                else:
                    break  # Detener la lectura al encontrar una fila vacía

            # Convertir las mediciones a un DataFrame para calcular max, min y rango
            df = pd.DataFrame(mediciones, columns=columnas)

            # Calcular Maximo, Minimo, Rango a partir de las columnas de medición (a partir de Fx en adelante)
            maximos = [''] * 2 + [df[col].max() for col in df.columns[3:]]
            minimos = [''] * 2 + [df[col].min() for col in df.columns[3:]]
            rangos = [''] * 2 + [(df[col].max() - df[col].min()) for col in df.columns[3:]]

            # Añadir los cálculos de Maximo, Minimo y Rango al archivo exportado
            with open("estudios/test1.txt", 'a') as output_file:
                for medicion in mediciones:
                    output_file.write(";".join(map(str, medicion)) + "\n")
                output_file.write(f";;MAXIMO;{';'.join(map(str, maximos[2:]))}\n")
                output_file.write(f";;MINIMO;{';'.join(map(str, minimos[2:]))}\n")
                output_file.write(f";;RANGO;{';'.join(map(str, rangos[2:]))}\n")

            print("Primera sección exportada correctamente en 'estudios/test1.txt'.")

            return True

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
