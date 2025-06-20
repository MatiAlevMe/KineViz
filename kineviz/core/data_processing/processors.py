from typing import List, Tuple
import pandas as pd # Importar pandas correctamente
import numpy as np
from scipy.interpolate import interp1d


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


def normalize_temporal_data(
    data_series: pd.Series,
    time_series: pd.Series,
    target_points: int = 101
) -> np.ndarray:
    """
    Normaliza una serie de datos temporales a un número específico de puntos (target_points).

    :param data_series: Serie de pandas con los datos a normalizar.
    :param time_series: Serie de pandas con los valores de tiempo correspondientes.
                        Se asume que está en segundos y es monótonicamente creciente.
    :param target_points: Número de puntos al que se normalizarán los datos (por defecto 101).
    :return: Un array de NumPy con los datos normalizados.
    :raises ValueError: Si las series de datos y tiempo no tienen la misma longitud,
                        o si no hay suficientes datos para interpolar.
    """
    if len(data_series) != len(time_series):
        raise ValueError("Las series de datos y tiempo deben tener la misma longitud.")
    if len(data_series) < 2: # Necesita al menos 2 puntos para interpolar
        raise ValueError("Se necesitan al menos dos puntos de datos para la interpolación.")

    # Asegurar que los datos de entrada sean arrays de NumPy
    data_array = data_series.to_numpy(dtype=float)
    time_array = time_series.to_numpy(dtype=float)

    # Crear una función de interpolación lineal
    # 'fill_value="extrapolate"' podría ser una opción si se necesita, pero
    # usualmente para normalización se interpola dentro del rango original.
    # 'bounds_error=False' junto con 'fill_value' puede manejar valores fuera del rango de tiempo original,
    # pero para normalización, el nuevo tiempo estará dentro del rango original.
    interpolation_function = interp1d(
        time_array,
        data_array,
        kind='linear', # Interpolación lineal es común para esto
        bounds_error=True # Asegura que solo se interpola dentro del rango de tiempo original
    )

    # Crear el nuevo vector de tiempo normalizado (0 a tiempo_maximo_original)
    # para los target_points.
    # Esto asegura que la interpolación se hace sobre la duración real del trial.
    min_time = time_array[0]
    max_time = time_array[-1]
    
    if max_time <= min_time and target_points > 1: # Evitar división por cero si el tiempo no avanza
        # Si el tiempo es constante, y se piden múltiples puntos,
        # se devuelve un array con el primer valor de datos repetido.
        # O se podría devolver el promedio, o lanzar un error.
        # Por ahora, repetimos el primer valor si es un solo punto de tiempo.
        # Si se espera una serie temporal, esto es un caso anómalo.
        # Si solo hay un punto de datos original, interp1d fallará antes.
        # Este caso es más para cuando todos los tiempos son iguales pero hay múltiples datos.
        return np.full(target_points, data_array[0])
    elif target_points == 1: # Si solo se quiere un punto, devolver el primero (o promedio)
        return np.array([data_array[0]])


    normalized_time_vector = np.linspace(min_time, max_time, target_points)

    # Aplicar la función de interpolación al nuevo vector de tiempo
    normalized_data = interpolation_function(normalized_time_vector)

    return normalized_data
