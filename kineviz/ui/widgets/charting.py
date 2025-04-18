import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np  # Para manejar posibles NaN
import pandas as pd # Necesario para formato de statannot/seaborn
import logging
import seaborn as sns
# Reintroducir statannot
from statannot import add_stat_annotation
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo

# Importar Plotly
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    # Configurar tema por defecto para Plotly (opcional)
    pio.templates.default = "plotly_white"
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


logger = logging.getLogger(__name__)  # Logger para este módulo


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


def create_interactive_comparison_boxplot(data_by_group: list, group_names: list[str],
                                          title: str, ylabel: str, output_path: Path):
    """
    Genera un gráfico de caja comparativo interactivo usando Plotly y lo guarda como HTML.
    NOTA: Actualmente no incluye anotaciones de significancia (NS, *, **).

    :param data_by_group: Lista de listas/arrays con datos numéricos por grupo.
    :param group_names: Lista de nombres para cada grupo (etiquetas eje X).
    :param title: Título del gráfico.
    :param ylabel: Etiqueta del eje Y.
    :param output_path: Ruta (Path object) donde guardar el gráfico HTML.
    """
    if not PLOTLY_AVAILABLE:
        logger.error("Plotly no está instalado. No se puede generar gráfico interactivo.")
        # Opcional: Crear un archivo HTML con un mensaje de error
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("<html><body><p>Error: La biblioteca Plotly no está instalada. "
                    "No se pudo generar el gráfico interactivo.</p></body></html>")
        return

    if len(data_by_group) != len(group_names):
        raise ValueError("Longitud de data_by_group y group_names no coinciden.")

    fig = go.Figure()

    # Colores consistentes con Seaborn Pastel1 si es posible
    try:
        palette = sns.color_palette("Pastel1", n_colors=len(group_names)).as_hex()
    except NameError: # Si seaborn no está disponible (poco probable aquí)
        palette = None

    valid_groups_exist = False
    for i, (group_name, group_data) in enumerate(zip(group_names, data_by_group)):
        # Convertir a array numpy y quitar NaNs
        numeric_data = np.array(group_data, dtype=float)
        cleaned_data = numeric_data[~np.isnan(numeric_data)]

        if cleaned_data.size > 0:
            valid_groups_exist = True
            fig.add_trace(go.Box(
                y=cleaned_data,
                name=group_name,
                boxpoints='all',  # Mostrar todos los puntos (similar a swarmplot)
                jitter=0.3,      # Añadir algo de dispersión horizontal
                pointpos=-1.8,   # Posicionar puntos a la izquierda
                marker_size=4,
                marker_color=palette[i] if palette else None,
                line_width=1
            ))
        else:
            logger.warning(f"Grupo '{group_name}' sin datos válidos para boxplot interactivo.")

    if not valid_groups_exist:
        logger.warning(f"No hay datos válidos para generar boxplot interactivo: {title}")
        # Crear un HTML vacío con mensaje
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><h3>{title}</h3><p>No hay datos válidos para comparar.</p></body></html>")
        return

    # Actualizar layout
    fig.update_layout(
        title=title,
        yaxis_title=ylabel,
        xaxis_title="Grupos Comparados",
        showlegend=True, # Mostrar leyenda por defecto
        legend_title_text='Grupos',
        boxmode='group', # Agrupar boxplots
        xaxis=dict(
            tickangle=30 # Rotar etiquetas eje X
        ),
        yaxis=dict(
            gridcolor='lightgrey', # Color de la cuadrícula Y
            zerolinecolor='grey'
        ),
        margin=dict(l=40, r=40, t=80, b=80), # Ajustar márgenes
    )

    # Guardar como HTML
    try:
        fig.write_html(output_path, include_plotlyjs='cdn') # Usar CDN para Plotly.js
        logger.info(f"Gráfico interactivo guardado en: {output_path}")
    except Exception as e:
        logger.error(f"Error guardando gráfico interactivo en {output_path}: {e}", exc_info=True)
        # Crear un archivo HTML con un mensaje de error si falla el guardado
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><p>Error al guardar el gráfico interactivo: {e}</p></body></html>")


def create_comparison_boxplot(data_by_group: list, group_names: list[str],
                              title: str, ylabel: str, output_path: Path,
                              stats_results=None):
    """
    Genera un gráfico de caja comparando múltiples grupos usando Seaborn y Statannot.

    :param data_by_group: Lista de listas/arrays con datos numéricos por grupo.
    :param group_names: Lista de nombres para cada grupo (etiquetas eje X).
    :param title: Título del gráfico.
    :param ylabel: Etiqueta del eje Y.
    :param output_path: Ruta (Path object) donde guardar el gráfico PNG.
    :param stats_results: Diccionario con resultados del test principal
                          {'test_name': str, 'p_value': float} o None.
    """
    if len(data_by_group) != len(group_names):
        raise ValueError("Longitud de data_by_group y group_names no coinciden.")

    # 1. Preparar datos en formato largo (DataFrame) para Seaborn/Statannot
    data_list = []
    for i, group_data in enumerate(data_by_group):
        group_name = group_names[i]
        # Convertir a array numpy y quitar NaNs
        numeric_data = np.array(group_data, dtype=float)
        cleaned_data = numeric_data[~np.isnan(numeric_data)]
        if cleaned_data.size > 0:
            for value in cleaned_data:
                data_list.append({'Group': group_name, 'Value': value})
        else:
            logger.warning(f"Grupo '{group_name}' sin datos válidos para boxplot.")

    if not data_list:
        logger.warning(f"No hay datos válidos para generar boxplot: {title}")
        # Crear gráfico vacío con mensaje (opcional)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No hay datos válidos para comparar',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes)
        ax.set_title(title)
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        plt.close(fig)
        return

    df_long = pd.DataFrame(data_list)
    # Asegurar que el orden de los grupos sea el original
    group_order = [name for name, data in zip(group_names, data_by_group)
                   if np.any(~np.isnan(np.array(data, dtype=float)))]

    # 2. Crear el gráfico base con Seaborn
    fig, ax = plt.subplots(figsize=(max(8, len(group_order) * 1.5), 6))
    palette = sns.color_palette("Pastel1", n_colors=len(group_order))

    # Boxplot
    sns.boxplot(data=df_long, x='Group', y='Value', order=group_order,
                palette=palette, showfliers=False, ax=ax, legend=False,
                boxprops=dict(alpha=.7)) # Añadir transparencia a cajas

    # Puntos individuales con swarmplot para mejor distribución
    sns.swarmplot(data=df_long, x='Group', y='Value', order=group_order,
                  palette=palette, # Usar misma paleta
                  edgecolor='gray', linewidth=0.5, # Contorno ligero
                  legend=False, ax=ax, size=4) # Ajustar tamaño

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Grupos Comparados") # Etiqueta genérica para X
    plt.xticks(rotation=30, ha="right")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 3. Añadir anotaciones estadísticas con statannot (si hay 2 grupos y p-valor)
    if stats_results and 'p_value' in stats_results and len(group_order) == 2:
        p_value = stats_results['p_value']
        if not np.isnan(p_value): # Solo si el p-valor es válido
            box_pairs = [(group_order[0], group_order[1])]
            try:
                add_stat_annotation(ax, data=df_long, x='Group', y='Value',
                                    order=group_order,
                                    box_pairs=box_pairs,
                                    test=None,  # Ya tenemos el p-valor
                                    perform_stat_test=False, # Indicar que no ejecute test
                                    text_format='star', # NS, *, **, ***
                                    pvalues=[p_value],
                                    loc='inside', verbose=0)
                logger.debug(f"Anotación statannot añadida para {title} "
                             f"con p={p_value}")
            except Exception as e_annot:
                # Si statannot falla, añadir texto simple como fallback
                logger.warning(f"Error al usar statannot para {title}: {e_annot}. "
                               f"Mostrando p-valor como texto.")
                test_name = stats_results.get('test_name', 'Test')
                if p_value < 0.001: p_text = "p < 0.001"
                else: p_text = f"p = {p_value:.3f}"
                plt.text(0.98, 0.98, f"{test_name}\n{p_text}",
                         verticalalignment='top', horizontalalignment='right',
                         transform=ax.transAxes, color='black', fontsize=9,
                         bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.5))
        else:
             logger.debug(f"P-valor no válido (NaN) para {title}, no se añaden anotaciones.")
    elif stats_results and 'p_value' in stats_results:
        # Si hay más de 2 grupos, mostrar p-valor general como texto (si es válido)
        p_value = stats_results['p_value']
        if not np.isnan(p_value):
            test_name = stats_results.get('test_name', 'Test')
            if p_value < 0.001: p_text = "p < 0.001"
            else: p_text = f"p = {p_value:.3f}"
            plt.text(0.98, 0.98, f"{test_name} (overall)\n{p_text}",
                     verticalalignment='top', horizontalalignment='right',
                     transform=ax.transAxes, color='black', fontsize=9,
                     bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.5))


    # 4. Añadir Leyenda
    # Crear handles (patches de color) para la leyenda
    handles = [plt.Rectangle((0,0),1,1, color=palette[i])
               for i in range(len(group_order))]
    # Colocar leyenda fuera del área del gráfico, a la derecha
    plt.legend(handles, group_order, title="Grupos",
               bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)


    # Ajustar layout para asegurar que todo quepa (incluida leyenda)
    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Ajustar rect para dejar espacio a la derecha

    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
