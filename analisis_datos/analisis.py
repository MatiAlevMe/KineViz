def calcular_tiempo(df, frecuencia):
    df['Tiempo'] = df.apply(lambda row: row.name * (1 / frecuencia), axis=1)
    return df

def calcular_maximo(df):
    return df.max()

def calcular_minimo(df):
    return df.min()

def calcular_rango(df):
    return df.max() - df.min()

def normalizar(df, columnas):
    for columna in columnas:
        df[columna] = df[columna] / (70 * 9.81)
    return df