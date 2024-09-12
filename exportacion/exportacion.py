def exportar_csv(df, nombre_archivo):
    df.to_csv(nombre_archivo, index=False, sep=';')

def generar_pdf(graficos, nombre_archivo):
    # Utilizar reportlab para crear un PDF con los gráficos
    # ...
