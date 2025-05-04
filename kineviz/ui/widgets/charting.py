import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np  # Para manejar posibles NaN
import pandas as pd # Necesario para formato de statannot/seaborn
import logging
import seaborn as sns
# Usar statannotations en lugar de statannot
# from statannot import add_stat_annotation # Ya no se usa
from statannotations.Annotator import Annotator # Importar Annotator
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


def create_interactive_comparison_boxplot(data_by_group: list,
                                          group_xaxis_labels: list[str],
                                          group_legend_names: list[str],
                                          title: str, ylabel: str, output_path: Path):
    """
    Genera un gráfico de caja comparativo interactivo usando Plotly y lo guarda como HTML.

    :param data_by_group: Lista de listas/arrays con datos numéricos por grupo.
    :param group_xaxis_labels: Lista de etiquetas cortas para el eje X ("Grupo 1", ...).
    :param group_legend_names: Lista de nombres descriptivos completos para leyenda/hover.
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

    # Corregir la validación de longitud
    if len(data_by_group) != len(group_xaxis_labels) or len(data_by_group) != len(group_legend_names):
        raise ValueError("Longitud de data_by_group y etiquetas de grupo no coinciden.")
    if len(group_xaxis_labels) != len(group_legend_names):
         raise ValueError("Longitud de etiquetas de eje X y leyenda no coinciden.")

    fig = go.Figure()

    # Colores consistentes con Seaborn Pastel1 si es posible
    try:
        palette = sns.color_palette("Pastel1", n_colors=len(group_xaxis_labels)).as_hex()
    except NameError: # Si seaborn no está disponible (poco probable aquí)
        palette = None

    valid_groups_exist = False
    # Iterar usando los nombres de leyenda y los datos
    for i, (legend_name, group_data) in enumerate(zip(group_legend_names, data_by_group)):
        # Convertir a array numpy y quitar NaNs
        numeric_data = np.array(group_data, dtype=float)
        cleaned_data = numeric_data[~np.isnan(numeric_data)]

        if cleaned_data.size > 0:
            valid_groups_exist = True
            # Usar legend_name para el nombre del trace (visible en hover/leyenda)
            fig.add_trace(go.Box(
                y=cleaned_data,
                name=legend_name, # Nombre completo para hover/leyenda
                x=[group_xaxis_labels[i]] * len(cleaned_data), # Asociar con etiqueta eje X
                boxpoints='all',  # Mostrar todos los puntos
                jitter=0.3,       # Mantener algo de jitter horizontal
                pointpos=0,       # Centrar puntos horizontalmente dentro de la caja
                marker_size=4,
                marker_color=palette[i] if palette else None,
                line_width=1
            ))
        else:
            # Usar legend_name en el log
            logger.warning(f"Grupo '{legend_name}' sin datos válidos para boxplot interactivo.")

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
        xaxis_title="", # Quitar título eje X
        showlegend=True, # Mostrar leyenda
        legend_title_text='Grupos', # Título para la leyenda
        boxmode='group',
        xaxis=dict(
            categoryorder='array', # Ordenar eje X según la lista proporcionada
            categoryarray=group_xaxis_labels, # Usar etiquetas cortas para ordenar
            tickmode='array',
            tickvals=group_xaxis_labels, # Usar etiquetas cortas para posiciones
            ticktext=group_xaxis_labels, # Usar etiquetas cortas para mostrar
            tickangle=30
        ),
        yaxis=dict(
            gridcolor='lightgrey', # Color de la cuadrícula Y
            zerolinecolor='grey'
        ),
        legend=dict(
            orientation="h", # Leyenda horizontal
            yanchor="bottom",
            y=-0.2, # Posición debajo del gráfico (ajustar si es necesario)
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=40, t=80, b=120), # Aumentar margen inferior para leyenda
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


def create_comparison_boxplot(data_by_group: list,
                              group_xaxis_labels: list[str],
                              group_legend_names: list[str],
                              title: str, ylabel: str, output_path: Path,
                              stats_results=None):
    """
    Genera un gráfico de caja comparando múltiples grupos usando Seaborn y Statannot.

    :param data_by_group: Lista de listas/arrays con datos numéricos por grupo.
    :param group_xaxis_labels: Lista de etiquetas cortas para el eje X ("Grupo 1", ...).
    :param group_legend_names: Lista de nombres descriptivos completos para leyenda.
    :param title: Título del gráfico.
    :param ylabel: Etiqueta del eje Y.
    :param output_path: Ruta (Path object) donde guardar el gráfico PNG.
    :param stats_results: Diccionario con resultados del test principal
                          {'test_name': str, 'p_value': float} o None.
    """
    if len(data_by_group) != len(group_xaxis_labels) or len(data_by_group) != len(group_legend_names):
        raise ValueError("Longitud de data_by_group y etiquetas de grupo no coinciden.")

    # 1. Preparar datos en formato largo (DataFrame) para Seaborn/Statannot
    data_list = []
    # Usar group_xaxis_labels para la columna 'Group' del DataFrame
    for i, group_data in enumerate(data_by_group):
        xaxis_label = group_xaxis_labels[i] # Etiqueta corta para agrupar
        legend_name = group_legend_names[i] # Nombre completo para referencia
        # Convertir a array numpy y quitar NaNs
        numeric_data = np.array(group_data, dtype=float)
        cleaned_data = numeric_data[~np.isnan(numeric_data)]
        if cleaned_data.size > 0:
            for value in cleaned_data:
                # Usar etiqueta corta en la columna 'Group'
                data_list.append({'Group': xaxis_label, 'Value': value})
        else:
            logger.warning(f"Grupo '{legend_name}' sin datos válidos para boxplot.")

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
    # Usar group_xaxis_labels para el orden y las etiquetas del eje X
    xaxis_order = [label for label, data in zip(group_xaxis_labels, data_by_group)
                   if np.any(~np.isnan(np.array(data, dtype=float)))]
    # Mapear etiquetas cortas a nombres completos para la leyenda
    legend_map = {xaxis_label: legend_name
                  for xaxis_label, legend_name in zip(group_xaxis_labels, group_legend_names)}

    # 2. Crear el gráfico base con Seaborn
    fig, ax = plt.subplots(figsize=(max(8, len(xaxis_order) * 1.5), 6))
    palette = sns.color_palette("Pastel1", n_colors=len(xaxis_order))

    # Boxplot - Usar xaxis_order para x y order, hue mapeado a nombres de leyenda
    sns.boxplot(data=df_long, x='Group', y='Value', order=xaxis_order,
                hue='Group', hue_order=xaxis_order, # Usar etiquetas cortas para hue
                palette=palette, showfliers=False, ax=ax, legend=False, # Ocultar leyenda interna
                boxprops=dict(alpha=.7))

    # Puntos individuales con swarmplot
    sns.swarmplot(data=df_long, x='Group', y='Value', order=xaxis_order,
                  hue='Group', hue_order=xaxis_order, # Usar etiquetas cortas para hue
                  palette=palette,
                  edgecolor='auto', linewidth=0.5,
                  legend=False, ax=ax, size=4) # Ocultar leyenda interna

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("") # Quitar etiqueta X
    # Usar etiquetas cortas para el eje X
    ax.set_xticks(range(len(xaxis_order)))
    ax.set_xticklabels(xaxis_order, rotation=30, ha="right")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 3. Añadir anotaciones estadísticas (usando xaxis_order)
    if stats_results and 'p_value' in stats_results and len(xaxis_order) == 2:
        p_value = stats_results['p_value']
        if not np.isnan(p_value):
            box_pairs = [(xaxis_order[0], xaxis_order[1])] # Usar etiquetas cortas
            try:
                # Configurar Annotator
                annotator = Annotator(ax, box_pairs, data=df_long,
                                      x='Group', y='Value', order=xaxis_order)
                annotator.configure(text_format='star', loc='inside', verbose=0)
                # Aplicar las anotaciones usando los p-valores precalculados
                annotator.set_pvalues_and_annotate([p_value])

                logger.debug(f"Anotación statannotations añadida para {title} "
                             f"con p={p_value}")
            except Exception as e_annot:
                # Si statannotations falla, añadir texto simple como fallback
                logger.warning(f"Error al usar statannotations para {title}: {e_annot}. "
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


    # 4. Añadir Leyenda (debajo del gráfico)
    handles = [plt.Rectangle((0,0),1,1, color=palette[i])
               for i in range(len(xaxis_order))]
    # Usar los group_legend_names pasados directamente
    legend_labels = group_legend_names
    # Colocar leyenda debajo, centrada, con múltiples columnas si es necesario
    fig.legend(handles, legend_labels, title="Grupos", loc='lower center',
               bbox_to_anchor=(0.5, -0.15), # Ajustar posición vertical (-0.15 o menos)
               ncol=min(len(legend_labels), 4), # Máximo 4 columnas
               frameon=False) # Sin borde


    # Ajustar layout para asegurar que todo quepa (incluida leyenda inferior)
    plt.tight_layout(rect=[0, 0.05, 1, 1]) # Ajustar rect para dejar espacio abajo

    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
