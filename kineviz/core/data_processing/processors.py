from typing import List, Tuple
import pandas as pd # Importar pandas correctamente

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
                                                                                                                                                               
def calcular_max_min_rango(df: pd.DataFrame, columnas: List[str]) -> Tuple[List, List, List]:
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
