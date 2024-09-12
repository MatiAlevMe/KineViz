import pandas as pd

def leer_archivo_csv_o_txt(ruta_archivo):
    try:
        with open(ruta_archivo, 'r') as file:
            # Leer la primera línea (cabecera)
            primera_fila = file.readline().rstrip()

            # Leer la segunda línea (número de frames)
            segunda_fila = file.readline().rstrip()
            num_frames = int(segunda_fila)
            print(f"Número de frames: {num_frames}")

            # Leer la tercera línea (atributos) y contar tabulaciones
            atributos = file.readline().rstrip("\n")
            atributos_separados = atributos.split("\t")  # Mantener las tabulaciones originales

            # Leer la cuarta línea (nombres de columnas)
            columnas = file.readline().rstrip("\n").split("\t")

            # Leer la quinta línea (unidades de medida)
            unidades = file.readline().rstrip("\n").split("\t")

            # Ajuste para la fila de atributos (considerando las separaciones correctas)
            atributos_finales = []
            for atributo in atributos_separados:
                if atributo.strip():  # Si hay texto en el atributo
                    atributos_finales.append(atributo)
                else:
                    atributos_finales.append('')  # Mantener las tabulaciones en blanco

            # Convertir cada lista en una cadena con separadores ";"
            atributos_str = ";".join(atributos_finales)
            columnas_str = ";".join(columnas)
            unidades_str = ";".join(unidades)

            # Exportar los datos leídos a un archivo separado por ";"
            with open("estudios/test1.txt", 'w') as output_file:
                output_file.write(f"{primera_fila}\n{segunda_fila}\n{atributos_str}\n{columnas_str}\n{unidades_str}\n")

            print("Primera sección exportada correctamente en 'estudios/test1.txt'.")

            return True

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
