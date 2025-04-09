import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np # Para manejar posibles NaN
import logging # Importar logging

# Asegurar que matplotlib no intente usar UI backend en entornos sin GUI
import matplotlib
matplotlib.use('Agg') # Usar backend no interactivo

logger = logging.getLogger(__name__) # Logger para este módulo

def create_boxplot(data_dict: dict, title: str, ylabel: str, output_path: Path):
    """
    Genera un gráfico de caja (boxplot) y lo guarda en la ruta especificada.

    :param data_dict: Diccionario donde las claves son etiquetas (ej. pacientes)
                      y los valores son listas de datos numéricos.
    :param title: Título del gráfico.
    :param ylabel: Etiqueta del eje Y.
    :param output_path: Ruta (Path object) donde guardar el gráfico PNG.
    """
    labels = list(data_dict.keys())
    # Filtrar listas vacías o con solo NaNs antes de pasar a boxplot
    data_to_plot = [np.array(d)[~np.isnan(d)] for d in data_dict.values() if np.any(~np.isnan(d))]
    valid_labels = [lbl for lbl, d in zip(labels, data_dict.values()) if np.any(~np.isnan(d))]

    if not data_to_plot:
        logger.warning(f"No hay datos válidos para generar boxplot: {title}")
        # Opcional: crear un gráfico vacío o con un mensaje
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No hay datos válidos', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title(title)
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.boxplot(data_to_plot, labels=valid_labels, showfliers=False) # Ocultar outliers por defecto
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right") # Mejorar legibilidad de etiquetas largas
    plt.tight_layout() # Ajustar layout para evitar solapamientos
    plt.savefig(output_path, bbox_inches='tight', dpi=150) # Guardar con resolución decente
    plt.close(fig) # Cerrar figura para liberar memoria

def create_barchart(data_dict: dict, title: str, xlabel: str, ylabel: str, output_path: Path):
    """
    Genera un gráfico de barras y lo guarda en la ruta especificada.

    :param data_dict: Diccionario donde las claves son etiquetas (ej. pacientes)
                      y los valores son los valores numéricos para las barras.
    :param title: Título del gráfico.
    :param xlabel: Etiqueta del eje X.
    :param ylabel: Etiqueta del eje Y.
    :param output_path: Ruta (Path object) donde guardar el gráfico PNG.
    """
    labels = list(data_dict.keys())
    values = list(data_dict.values())

    if not values:
        logger.warning(f"No hay datos válidos para generar barchart: {title}")
        # Opcional: crear un gráfico vacío o con un mensaje
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No hay datos válidos', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title(title)
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
