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

            # Ajustar y convertir las filas leídas en cadenas separadas por ';'
            atributos_str = ajustar_fila(atributos_separados)
            columnas_str = ajustar_fila(columnas)
            unidades_str = ajustar_fila(unidades)

            # Exportar las primeras 5 filas en formato separado por ";"
            with open("estudios/test1.txt", 'w') as output_file:
                output_file.write(f"{primera_fila}\n{segunda_fila}\n{atributos_str}\n{columnas_str}\n{unidades_str}\n")

            print("Primera sección exportada correctamente en 'estudios/test1.txt'.")

            return True

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
