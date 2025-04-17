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

def create_comparison_boxplot(data_by_group: list, group_names: list[str], title: str, ylabel: str, output_path: Path, stats_results=None):
    """
    Genera un gráfico de caja comparando múltiples grupos.

    :param data_by_group: Lista de listas/arrays, donde cada elemento interno
                          contiene los datos numéricos para un grupo.
    :param group_names: Lista de nombres para cada grupo (etiquetas eje X).
    :param title: Título del gráfico.
    :param ylabel: Etiqueta del eje Y.
    :param output_path: Ruta (Path object) donde guardar el gráfico PNG.
    :param stats_results: Diccionario opcional con resultados estadísticos para anotar. (No implementado aún)
    """
    if len(data_by_group) != len(group_names):
        raise ValueError("La longitud de data_by_group debe coincidir con group_names.")

    # Filtrar grupos sin datos válidos (solo NaNs o vacíos)
    valid_data = []
    valid_labels = []
    for data, label in zip(data_by_group, group_names):
        # Convertir a array numpy y quitar NaNs
        numeric_data = np.array(data, dtype=float) # Asegurar tipo float
        cleaned_data = numeric_data[~np.isnan(numeric_data)]
        if cleaned_data.size > 0: # Verificar si quedan datos después de quitar NaNs
            valid_data.append(cleaned_data)
            valid_labels.append(label)
        else:
             logger.warning(f"Grupo '{label}' no contiene datos válidos para el boxplot comparativo '{title}'.")

    if not valid_data:
        logger.warning(f"No hay datos válidos en ningún grupo para generar boxplot comparativo: {title}")
        # Crear gráfico vacío con mensaje
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No hay datos válidos para comparar', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title(title)
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(max(8, len(valid_labels) * 1.5), 6)) # Ajustar ancho dinámicamente
    bp = ax.boxplot(valid_data, labels=valid_labels, showfliers=False, patch_artist=True) # patch_artist para colorear

    # Colorear cajas (opcional)
    colors = plt.cm.get_cmap('Pastel1', len(valid_data))
    for patch, color in zip(bp['boxes'], colors(range(len(valid_data)))):
        patch.set_facecolor(color)

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=30, ha="right") # Rotar etiquetas si son muchas/largas
    plt.grid(axis='y', linestyle='--', alpha=0.7) # Añadir rejilla horizontal
    plt.tight_layout()

    # --- Anotaciones Estadísticas (Placeholder) ---
    if stats_results:
        # TODO: Implementar lógica para añadir p-values o marcadores de significancia
        # basado en el contenido de stats_results.
        # Esto puede requerir librerías adicionales como statannot.
        logger.info("Anotaciones estadísticas solicitadas pero aún no implementadas.")
        pass

    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
