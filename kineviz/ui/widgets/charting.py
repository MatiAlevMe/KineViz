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
import scipy.stats # Para calcular IC

# Importar Plotly
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    from plotly.subplots import make_subplots # Correct import
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

    # Panel Superior: Curvas Promedio +/- EEM, DE o IC
    ax_mean_curves = axs[0]
    colors = plt.cm.get_cmap('viridis', len(group_keys)) # Color map

    # Determinar globalmente qué tipo de sombreado se usará para el título y qué rellenar
    show_ci_global = spm_results.get('show_conf_int', False)
    show_std_global = spm_results.get('show_std_dev', False)
    show_sem_global = spm_results.get('show_sem', False) # New flag for SEM

    global_fill_type_label = "" # Default to no label if no fill
    fill_active = False

    if show_ci_global:
        global_fill_type_label = "± 95% IC"
        fill_active = True
    elif show_std_global:
        global_fill_type_label = "± DE"
        fill_active = True
    elif show_sem_global:
        global_fill_type_label = "± EEM"
        fill_active = True

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
            
            lower_bound = None
            upper_bound = None
            
            num_subjects_in_group = stacked_data.shape[0]
            if num_subjects_in_group > 0:
                sem_curve = std_dev_curve / np.sqrt(num_subjects_in_group) # Always calculate SEM

                if show_ci_global and num_subjects_in_group > 1:
                    confidence_level = 0.95
                    degrees_freedom = num_subjects_in_group - 1
                    t_critical = scipy.stats.t.ppf((1 + confidence_level) / 2, df=degrees_freedom)
                    ci_margin = t_critical * sem_curve
                    lower_bound = mean_curve - ci_margin
                    upper_bound = mean_curve + ci_margin
                elif show_std_global:
                    lower_bound = mean_curve - std_dev_curve
                    upper_bound = mean_curve + std_dev_curve
                elif show_sem_global: # New condition for SEM
                    lower_bound = mean_curve - sem_curve
                    upper_bound = mean_curve + sem_curve
                # If no flag is true, lower_bound and upper_bound remain None
            
            ax_mean_curves.plot(time_axis, mean_curve, label=group_legend_names[i], color=colors(i/len(group_keys)), linewidth=2)
            if fill_active and lower_bound is not None and upper_bound is not None: # Only fill if a type is active
                ax_mean_curves.fill_between(time_axis, lower_bound, upper_bound,
                                            color=colors(i/len(group_keys)), alpha=0.2)
        except Exception as e:
            logger.error(f"Error procesando datos para graficar grupo '{group_legend_names[i]}': {e}", exc_info=True)

    ax_mean_curves.set_ylabel(variable_name)
    ax_mean_curves.legend(loc='best', fontsize='small')
    ax_mean_curves.set_title(f'Curvas Temporales Promedio {global_fill_type_label}'.strip()) # Use strip to remove trailing space if label is empty
    ax_mean_curves.grid(True, linestyle='-', alpha=0.7) # Grid con líneas continuas

    # Panel Inferior: Curva Estadística SPM
    ax_spm_stat = axs[1]
    ax_spm_stat.grid(True, linestyle='-', alpha=0.7) # Grid con líneas continuas
    stat_curve = spm_results.get('stat_curve') # Ensure stat_curve is a list or np.array
    if stat_curve is not None and not isinstance(stat_curve, (list, np.ndarray)):
        logger.warning(f"stat_curve is not a list or ndarray: {type(stat_curve)}. Plotting may fail.")
        stat_curve = None # Prevent error if it's not array-like

    critical_threshold = spm_results.get('critical_threshold')
    clusters = spm_results.get('clusters', [])
    test_type = spm_results.get('test_type', 'SPM').upper()
    df_stat = spm_results.get('df', '')

    if stat_curve:
        ax_spm_stat.plot(time_axis, stat_curve, color='black', linewidth=1.5, label=f'Estadístico {test_type}')
        
        if critical_threshold is not None:
            ax_spm_stat.axhline(critical_threshold, color='red', linestyle='--', linewidth=1, label=f'Umbral Crítico (α={spm_results.get("alpha_level", 0.05)})')
            # For two-tailed t-tests, also plot -critical_threshold if applicable
            if "ttest" in test_type.lower() and critical_threshold > 0 : # Check if it's a t-test and threshold is positive
                 ax_spm_stat.axhline(-critical_threshold, color='red', linestyle='--', linewidth=1)


        # Resaltar clusters significativos
        if clusters:
            # Asegurarse de que la etiqueta de cluster solo se añada una vez
            first_cluster_labeled = False
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
                    ymin_plot, ymax_plot = ax_spm_stat.get_ylim()
                    
                    current_cluster_label_for_legend = None
                    if not first_cluster_labeled:
                        current_cluster_label_for_legend = 'Cluster(s) Significativo(s)'
                        first_cluster_labeled = True
                        
                    ax_spm_stat.fill_betweenx(y=[ymin_plot, ymax_plot], x1=time_start, x2=time_end,
                                              color='lightcoral', alpha=0.3,
                                              label=current_cluster_label_for_legend)

                    # --- Annotate cluster details (Peak Stat, Cluster P, Time of Peak) --- (Conditional)
                    if spm_results.get('annotate_spm_clusters_bottom', True):
                        peak_node = cluster.get('peak_node')
                        peak_value = cluster.get('peak_value')
                    cluster_p_val = cluster.get('p_value')

                    if peak_node is not None and peak_value is not None and cluster_p_val is not None and \
                       peak_node < len(time_axis) and stat_curve is not None and peak_node < len(stat_curve):
                        
                        time_of_peak = time_axis[peak_node]
                        actual_peak_stat_on_curve = stat_curve[peak_node] # Use actual value from curve for positioning

                        annotation_text = (f"Peak Stat: {peak_value:.2f}\n"
                                           f"Cluster p: {cluster_p_val:.3f}\n"
                                           f"Time: {time_of_peak:.1f}%")
                        
                        # Position annotation near the peak
                        # Heuristic for y_offset: place above if peak is positive, below if negative
                        y_offset_factor = 0.1 * (ymax_plot - ymin_plot)
                        text_y = actual_peak_stat_on_curve + y_offset_factor if actual_peak_stat_on_curve >= 0 else actual_peak_stat_on_curve - y_offset_factor * 2
                        
                        # Ensure text is within plot bounds
                        if text_y > ymax_plot * 0.95: text_y = ymax_plot * 0.95
                        if text_y < ymin_plot + (ymax_plot - ymin_plot) * 0.05 : text_y = ymin_plot + (ymax_plot - ymin_plot) * 0.05


                        ax_spm_stat.plot(time_of_peak, actual_peak_stat_on_curve, 'o', color='blue', markersize=5)
                        ax_spm_stat.annotate(annotation_text,
                                             xy=(time_of_peak, actual_peak_stat_on_curve),
                                             xytext=(time_of_peak, text_y),
                                             ha='center', va='center', fontsize='x-small',
                                             arrowprops=dict(facecolor='black', shrink=0.05, width=0.5, headwidth=4),
                                             bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7, ec='grey'))
                    
                    # --- Annotate top plot (mean curves) with significant cluster range --- (Conditional)
                    if spm_results.get('annotate_spm_range_top', True):
                        # Get y-range of the top plot to position the bar
                        top_ymin, top_ymax = ax_mean_curves.get_ylim()
                        bar_height = (top_ymax - top_ymin) * 0.03 # Small height for the bar
                        bar_y_position = top_ymin - bar_height * 1.5 # Position below the y-axis data range

                        ax_mean_curves.fill_between([time_start, time_end], 
                                                    [bar_y_position - bar_height/2, bar_y_position - bar_height/2],
                                                    [bar_y_position + bar_height/2, bar_y_position + bar_height/2],
                                                    color='lightcoral', alpha=0.5, 
                                                    label='Rango Significativo (SPM)' if current_cluster_label_for_legend else None, # Label only once
                                                    transform=ax_mean_curves.get_xaxis_transform()) # Relative to x-axis, data coords for y

                else:
                    logger.warning(f"Nodos de cluster inválidos o fuera de rango: {cluster}. No se resaltará.")
        
        # Update legend for top plot if new items were added
        handles_top, labels_top = ax_mean_curves.get_legend_handles_labels()
        if any("Rango Significativo" in lab for lab in labels_top): # Check if new label was added
            # Filter out duplicate "Rango Significativo" labels if fill_between added it multiple times
            unique_handles_labels = {}
            for h, l in zip(handles_top, labels_top):
                if l not in unique_handles_labels:
                    unique_handles_labels[l] = h
            ax_mean_curves.legend(unique_handles_labels.values(), unique_handles_labels.keys(), loc='best', fontsize='small')


        ax_spm_stat.legend(loc='best', fontsize='small')
    else:
        ax_spm_stat.text(0.5, 0.5, 'Curva de estadístico SPM no disponible.', ha='center', va='center', transform=ax_spm_stat.transAxes)

    stat_label = f'Estadístico {test_type}'
    if df_stat:
        df_str = ', '.join(map(str, df_stat))
        stat_label += f' (gl={df_str})' # gl para grados de libertad
    ax_spm_stat.set_ylabel(stat_label)
    ax_spm_stat.set_xlabel('Tiempo Normalizado (%)')
    ax_spm_stat.set_title('Análisis Estadístico SPM')

    fig.tight_layout(pad=2.0) # Add some padding between subplots and title
    
    # --- Time Range Delimitation and Labeling ---
    main_title_text = f'Análisis SPM: {variable_name}'
    if spm_results.get('delimit_time_range', False):
        time_min = spm_results.get('time_min', 0.0)
        time_max = spm_results.get('time_max', 100.0)
        
        if spm_results.get('show_full_time_with_delimiters', True):
            for ax_panel in axs: # Apply to both top and bottom panels
                ax_panel.axvline(time_min, color='blue', linestyle=':', linewidth=1.2, alpha=0.8)
                ax_panel.axvline(time_max, color='blue', linestyle=':', linewidth=1.2, alpha=0.8)
        else: # Zoom into the range
            for ax_panel in axs:
                ax_panel.set_xlim(time_min, time_max)
        
        if spm_results.get('add_time_range_label', False) and spm_results.get('time_range_label_text', ''):
            time_label = spm_results.get('time_range_label_text')
            main_title_text += f" ({time_label}: {time_min:.0f}-{time_max:.0f}%)"

    fig.suptitle(main_title_text, fontsize=16, y=0.99) # Overall title, adjust y if needed
    plt.subplots_adjust(top=0.92) # Adjust top to make space for suptitle

    try:
        plt.savefig(output_path, bbox_inches='tight', dpi=150)
        logger.info(f"Gráfico SPM guardado en: {output_path}")
    except Exception as e:
        logger.error(f"Error guardando gráfico SPM en {output_path}: {e}", exc_info=True)
    finally:
        plt.close(fig)


def create_interactive_spm_results_plot(normalized_data_by_group: dict,
                                        spm_results: dict,
                                        group_legend_names: list[str],
                                        variable_name: str,
                                        output_path: Path):
    """
    Generates an interactive two-panel plot for SPM analysis results using Plotly.
    Top panel: Mean curves +/- SEM/STD/CI for each group.
    Bottom panel: SPM statistic curve, critical threshold, and significant clusters.

    :param normalized_data_by_group: Dict {group_key: list_of_np_arrays (101,)}.
    :param spm_results: Dict from AnalysisService, containing display options,
                        'stat_curve', 'critical_threshold', 'clusters', etc.
    :param group_legend_names: List of display names for the groups.
    :param variable_name: Name of the analyzed variable for y-axis label.
    :param output_path: Path object to save the HTML plot.
    """
    if not PLOTLY_AVAILABLE:
        logger.error("Plotly no está instalado. No se puede generar gráfico SPM interactivo.")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("<html><body><p>Error: La biblioteca Plotly no está instalada. "
                    "No se pudo generar el gráfico interactivo.</p></body></html>")
        return

    logger.debug(f"Generando gráfico SPM interactivo para variable '{variable_name}' en {output_path}")

    if not normalized_data_by_group or not group_legend_names:
        logger.warning("No hay datos normalizados o nombres de grupo para generar gráfico SPM interactivo.")
        # Create an empty HTML file with a message
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><h3>Análisis SPM: {variable_name}</h3>"
                    "<p>No hay datos normalizados o nombres de grupo para generar el gráfico.</p></body></html>")
        return

    group_keys = list(normalized_data_by_group.keys())
    if len(group_keys) != len(group_legend_names):
        logger.error("Discrepancia en número de grupos entre datos normalizados y nombres de leyenda para gráfico interactivo.")
        group_legend_names = group_keys # Fallback

    num_points = 101
    time_axis = np.linspace(0, 100, num_points)

    fig = go.Figure() # Default in case make_subplots fails
    try:
        # Initialize with template and make subplots
        fig = make_subplots( # Correct function call
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.05, # Adjust spacing between subplots
            row_heights=[0.6, 0.4], # Allocate more space to mean curves
            figure=go.Figure(layout=go.Layout(template="plotly_white")) # Pass initial figure with template
        )
    except Exception as e_subplot:
        logger.error(f"Error creando subplots con Plotly: {e_subplot}. Usando figura simple.", exc_info=True)
        # Fallback to a simple figure if make_subplots fails
        fig = go.Figure(layout=go.Layout(template="plotly_white"))


    # Determine global fill type for title
    show_ci_global = spm_results.get('show_conf_int', False)
    show_std_global = spm_results.get('show_std_dev', False)
    # Default SEM to True if others are false, or if explicitly set
    show_sem_global = spm_results.get('show_sem', not (show_ci_global or show_std_global))

    global_fill_type_label = ""
    if show_ci_global: global_fill_type_label = "± 95% IC"
    elif show_std_global: global_fill_type_label = "± DE"
    elif show_sem_global: global_fill_type_label = "± EEM"


    # --- Panel Superior: Curvas Promedio ---
    color_sequence = pio.templates[pio.templates.default].layout.colorway or go.colors.DEFAULT_PLOTLY_COLORS

    for i, group_key in enumerate(group_keys):
        group_data_arrays = normalized_data_by_group[group_key]
        if not group_data_arrays: continue

        try:
            stacked_data = np.stack(group_data_arrays, axis=0)
            mean_curve = np.mean(stacked_data, axis=0)
            std_dev_curve = np.std(stacked_data, axis=0, ddof=1)
            
            lower_bound, upper_bound = None, None
            num_subjects_in_group = stacked_data.shape[0]

            if num_subjects_in_group > 0:
                sem_curve = std_dev_curve / np.sqrt(num_subjects_in_group)
                if show_ci_global and num_subjects_in_group > 1:
                    t_critical = scipy.stats.t.ppf((1 + 0.95) / 2, df=num_subjects_in_group - 1)
                    ci_margin = t_critical * sem_curve
                    lower_bound, upper_bound = mean_curve - ci_margin, mean_curve + ci_margin
                elif show_std_global:
                    lower_bound, upper_bound = mean_curve - std_dev_curve, mean_curve + std_dev_curve
                elif show_sem_global: # This will be true if it's the default or explicitly chosen
                    lower_bound, upper_bound = mean_curve - sem_curve, mean_curve + sem_curve

            color = color_sequence[i % len(color_sequence)]
            fig.add_trace(go.Scatter(
                x=time_axis, y=mean_curve, name=group_legend_names[i],
                legendgroup=f"group{i}",
                line=dict(color=color, width=2),
                mode='lines'
            ), row=1, col=1)

            if lower_bound is not None and upper_bound is not None:
                # Convert hex color to rgba for fillcolor
                r_hex, g_hex, b_hex = color[1:3], color[3:5], color[5:7]
                fill_rgba_color = f'rgba({int(r_hex,16)},{int(g_hex,16)},{int(b_hex,16)},0.2)'
                
                fig.add_trace(go.Scatter(
                    x=np.concatenate([time_axis, time_axis[::-1]]), 
                    y=np.concatenate([upper_bound, lower_bound[::-1]]), 
                    fill='toself',
                    fillcolor=fill_rgba_color,
                    line=dict(width=0),
                    name=f"{group_legend_names[i]} {global_fill_type_label}",
                    legendgroup=f"group{i}",
                    showlegend=False 
                ), row=1, col=1)
        except Exception as e_trace:
            logger.error(f"Error añadiendo trace para grupo '{group_legend_names[i]}' en gráfico interactivo: {e_trace}", exc_info=True)

    # --- Panel Inferior: Curva Estadística SPM ---
    stat_curve = spm_results.get('stat_curve')
    critical_threshold = spm_results.get('critical_threshold')
    clusters = spm_results.get('clusters', [])
    test_type = spm_results.get('test_type', 'SPM').upper()
    df_stat = spm_results.get('df', '')
    alpha_level = spm_results.get('alpha_level', 0.05)

    if stat_curve is not None:
        fig.add_trace(go.Scatter(
            x=time_axis, y=stat_curve, name=f'Estadístico {test_type}',
            line=dict(color='black', width=1.5),
            mode='lines'
        ), row=2, col=1)

        if critical_threshold is not None:
            fig.add_hline(y=critical_threshold, line_dash="dash", line_color="red",
                          annotation_text=f'Umbral Crítico (α={alpha_level})',
                          annotation_position="bottom right", row=2, col=1)
            if "ttest" in test_type.lower() and critical_threshold > 0:
                 fig.add_hline(y=-critical_threshold, line_dash="dash", line_color="red", row=2, col=1)
        
        if clusters and spm_results.get('annotate_spm_clusters_bottom', True):
            for i_clus, cluster in enumerate(clusters):
                start_node, end_node = cluster.get('start_node'), cluster.get('end_node')
                if start_node is not None and end_node is not None and \
                   start_node < len(time_axis) and end_node < len(time_axis) and start_node <= end_node:
                    
                    time_start, time_end = time_axis[start_node], time_axis[end_node]
                    fig.add_vrect(
                        x0=time_start, x1=time_end,
                        fillcolor="lightcoral", opacity=0.3,
                        layer="below", line_width=0,
                        name=f'Cluster Sig. {i_clus+1}' if i_clus == 0 else None, 
                        showlegend= i_clus == 0, 
                        row=2, col=1
                    )
                    peak_node, peak_value, p_val = cluster.get('peak_node'), cluster.get('peak_value'), cluster.get('p_value')
                    if peak_node is not None and peak_value is not None and p_val is not None and peak_node < len(time_axis) and peak_node < len(stat_curve):
                        time_of_peak = time_axis[peak_node]
                        actual_peak_stat = stat_curve[peak_node]
                        fig.add_annotation(
                            x=time_of_peak, y=actual_peak_stat,
                            text=(f"Peak: {peak_value:.2f}<br>"
                                  f"p: {p_val:.3f}<br>"
                                  f"t: {time_of_peak:.1f}%"),
                            showarrow=True, arrowhead=1, arrowcolor="blue",
                            ax=0, ay=-40 if actual_peak_stat >=0 else 40, 
                            bgcolor="rgba(255,255,255,0.7)", bordercolor="grey", borderwidth=1,
                            row=2, col=1
                        )
                        fig.add_trace(go.Scatter(
                            x=[time_of_peak], y=[actual_peak_stat], mode='markers',
                            marker=dict(color='blue', size=5), showlegend=False
                        ), row=2, col=1)

    if clusters and spm_results.get('annotate_spm_range_top', True):
        for i_clus_top, cluster_top in enumerate(clusters):
            start_node_top, end_node_top = cluster_top.get('start_node'), cluster_top.get('end_node')
            if start_node_top is not None and end_node_top is not None and \
               start_node_top < len(time_axis) and end_node_top < len(time_axis) and start_node_top <= end_node_top:
                time_start_top, time_end_top = time_axis[start_node_top], time_axis[end_node_top]
                fig.add_shape(type="rect",
                    xref="x1", yref="paper", 
                    x0=time_start_top, y0=0, 
                    x1=time_end_top, y1=0.03, 
                    fillcolor="lightcoral", opacity=0.5,
                    layer="below", line_width=0,
                    name=f'Rango Sig. (SPM) {i_clus_top+1}' if i_clus_top == 0 else None,
                    row=1, col=1 # Apply to top plot
                )
                # Add to legend only once for the top plot annotation
                if i_clus_top == 0:
                    fig.add_trace(go.Scatter(
                        x=[None], y=[None], # Dummy trace for legend
                        mode='markers',
                        marker=dict(color='lightcoral', size=10, symbol='square', opacity=0.5),
                        legendgroup="spm_range_top",
                        showlegend=True,
                        name='Rango Significativo (SPM)'
                    ), row=1, col=1)


    # --- Layout y Títulos ---
    main_title_text = f'Análisis SPM Interactivo: {variable_name}'
    if spm_results.get('delimit_time_range', False):
        time_min, time_max = spm_results.get('time_min', 0.0), spm_results.get('time_max', 100.0)
        if spm_results.get('show_full_time_with_delimiters', True):
            fig.add_vline(x=time_min, line_dash="dot", line_color="blue", row="all", col=1)
            fig.add_vline(x=time_max, line_dash="dot", line_color="blue", row="all", col=1)
        else:
            # Apply to all x-axes. For shared axes, this should set the desired range.
            fig.update_xaxes(range=[time_min, time_max]) 
        
        if spm_results.get('add_time_range_label', False) and spm_results.get('time_range_label_text', ''):
            time_label = spm_results.get('time_range_label_text')
            main_title_text += f" ({time_label}: {time_min:.0f}-{time_max:.0f}%)"

    fig.update_layout(
        title_text=main_title_text, title_x=0.5,
        legend_title_text='Grupos',
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), 
        margin=dict(l=60, r=30, t=80, b=180) # Increased bottom margin
    )

    fig.update_yaxes(title_text=variable_name, row=1, col=1, gridcolor='lightgrey', zerolinecolor='grey')
    stat_label = f'Estadístico {test_type}'
    if df_stat: stat_label += f' (gl={", ".join(map(str, df_stat))})'
    fig.update_yaxes(title_text=stat_label, row=2, col=1, gridcolor='lightgrey', zerolinecolor='grey')
    fig.update_xaxes(title_text='Tiempo Normalizado (%)', row=2, col=1, gridcolor='lightgrey')
    fig.update_xaxes(row=1, col=1, gridcolor='lightgrey') # Ensure top x-axis also has grid

    try:
        fig.write_html(output_path, include_plotlyjs='cdn')
        logger.info(f"Gráfico SPM interactivo guardado en: {output_path}")
    except Exception as e_save:
        logger.error(f"Error guardando gráfico SPM interactivo en {output_path}: {e_save}", exc_info=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><p>Error al guardar el gráfico interactivo: {e_save}</p></body></html>")


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
