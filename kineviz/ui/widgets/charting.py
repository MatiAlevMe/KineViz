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


def create_spm_results_plot(normalized_data_by_group: dict,
                              spm_results: dict,
                              group_legend_names: list[str],
                              variable_name: str,
                              output_path: Path):
    """
    Generates a two-panel plot for SPM analysis results.
    Top panel: Mean curves +/- SEM for each group.
    Bottom panel: SPM statistic curve, critical threshold, and significant clusters.

    :param normalized_data_by_group: Dict {group_key: list_of_np_arrays (101,)}.
                                     Order of keys should match group_legend_names.
    :param spm_results: Dict from AnalysisService, containing 'stat_curve',
                        'critical_threshold', 'clusters', 'test_type', 'df'.
    :param group_legend_names: List of display names for the groups.
    :param variable_name: Name of the analyzed variable for y-axis label.
    :param output_path: Path object to save the PNG plot.
    """
    logger.debug(f"Generando gráfico SPM para variable '{variable_name}' en {output_path}")

    if not normalized_data_by_group or not group_legend_names:
        logger.warning("No hay datos normalizados o nombres de grupo para generar gráfico SPM.")
        return

    group_keys = list(normalized_data_by_group.keys())
    if len(group_keys) != len(group_legend_names):
        logger.error("Discrepancia en número de grupos entre datos normalizados y nombres de leyenda.")
        # Fallback: try to use original keys if legend names mismatch
        if len(group_keys) == len(next(iter(normalized_data_by_group.values()), [])): # Check if data matches group_keys
             group_legend_names = group_keys
        else: # Cannot reconcile, abort plotting
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, 'Error: Datos de grupo inconsistentes', ha='center', va='center', transform=ax.transAxes)
            plt.savefig(output_path, bbox_inches='tight', dpi=150)
            plt.close(fig)
            return


    num_points = 101 # Assuming data is normalized to 101 points
    time_axis = np.linspace(0, 100, num_points)

    fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    plt.style.use('seaborn-v0_8-whitegrid') # Using a seaborn style

    # Panel Superior: Curvas Promedio +/- SEM
    ax_mean_curves = axs[0]
    colors = plt.cm.get_cmap('viridis', len(group_keys)) # Color map

    for i, group_key in enumerate(group_keys):
        group_data_arrays = normalized_data_by_group[group_key]
        if not group_data_arrays:
            logger.warning(f"No hay arrays de datos para el grupo '{group_legend_names[i]}'.")
            continue
        
        # Stack arrays to compute mean and sem along axis 0 (across trials/subjects)
        try:
            stacked_data = np.stack(group_data_arrays, axis=0) # Shape: (num_trials, num_points)
            mean_curve = np.mean(stacked_data, axis=0)
            std_dev_curve = np.std(stacked_data, axis=0, ddof=1) # ddof=1 for sample std dev
            sem_curve = std_dev_curve / np.sqrt(stacked_data.shape[0])
            
            ax_mean_curves.plot(time_axis, mean_curve, label=group_legend_names[i], color=colors(i/len(group_keys)), linewidth=2)
            ax_mean_curves.fill_between(time_axis, mean_curve - sem_curve, mean_curve + sem_curve,
                                        color=colors(i/len(group_keys)), alpha=0.2)
        except Exception as e:
            logger.error(f"Error procesando datos para graficar grupo '{group_legend_names[i]}': {e}", exc_info=True)


    ax_mean_curves.set_ylabel(variable_name)
    ax_mean_curves.legend(loc='best', fontsize='small')
    ax_mean_curves.set_title('Mean Temporal Curves ± SEM')

    # Panel Inferior: Curva Estadística SPM
    ax_spm_stat = axs[1]
    stat_curve = spm_results.get('stat_curve')
    critical_threshold = spm_results.get('critical_threshold')
    clusters = spm_results.get('clusters', [])
    test_type = spm_results.get('test_type', 'SPM').upper()
    df_stat = spm_results.get('df', '')

    if stat_curve:
        ax_spm_stat.plot(time_axis, stat_curve, color='black', linewidth=1.5, label=f'{test_type} Statistic')
        
        if critical_threshold is not None:
            ax_spm_stat.axhline(critical_threshold, color='red', linestyle='--', linewidth=1, label=f'Critical Threshold (α={spm_results.get("alpha_level", 0.05)})')
            # For two-tailed t-tests, also plot -critical_threshold if applicable
            if "ttest" in test_type.lower() and critical_threshold > 0 : # Check if it's a t-test and threshold is positive
                 ax_spm_stat.axhline(-critical_threshold, color='red', linestyle='--', linewidth=1)


        # Resaltar clusters significativos
        if clusters:
            for cluster in clusters:
                start_node = cluster.get('start_node')
                end_node = cluster.get('end_node')
                # Ensure nodes are within bounds of time_axis
                if start_node is not None and end_node is not None and \
                   start_node < len(time_axis) and end_node < len(time_axis) and start_node <= end_node:
                    
                    # Map node indices to time values for fill_betweenx
                    time_start = time_axis[start_node]
                    time_end = time_axis[end_node]

                    # Get y-limits for shading
                    ymin, ymax = ax_spm_stat.get_ylim()
                    
                    ax_spm_stat.fill_betweenx(y=[ymin, ymax], x1=time_start, x2=time_end,
                                              color='lightcoral', alpha=0.3,
                                              label='Significant Cluster(s)' if cluster == clusters[0] else None) # Label only first
                else:
                    logger.warning(f"Nodos de cluster inválidos o fuera de rango: {cluster}. No se resaltará.")


        ax_spm_stat.legend(loc='best', fontsize='small')
    else:
        ax_spm_stat.text(0.5, 0.5, 'SPM statistic curve not available.', ha='center', va='center', transform=ax_spm_stat.transAxes)

    stat_label = f'{test_type} Statistic'
    if df_stat:
        df_str = ', '.join(map(str, df_stat))
        stat_label += f' (df={df_str})'
    ax_spm_stat.set_ylabel(stat_label)
    ax_spm_stat.set_xlabel('Normalized Time (%)')
    ax_spm_stat.set_title('SPM Statistical Analysis')

    fig.tight_layout(pad=2.0) # Add some padding between subplots and title
    fig.suptitle(f'SPM Analysis: {variable_name}', fontsize=16, y=0.99) # Overall title, adjust y if needed
    plt.subplots_adjust(top=0.92) # Adjust top to make space for suptitle

    try:
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        logger.info(f"Gráfico SPM guardado en: {output_path}")
    except Exception as e:
        logger.error(f"Error guardando gráfico SPM en {output_path}: {e}", exc_info=True)
    finally:
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
