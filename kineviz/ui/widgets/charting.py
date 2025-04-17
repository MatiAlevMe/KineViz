import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np  # Para manejar posibles NaN
import pandas as pd # Necesario para formato de statannot/seaborn
import logging  # Importar logging
import seaborn as sns # Importar Seaborn
from statannot import add_stat_annotation # Importar statannot

# Asegurar que matplotlib no intente usar UI backend en entornos sin GUI
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo

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
                palette=palette, showfliers=False, ax=ax, legend=False)

    # Puntos individuales con jitter
    sns.stripplot(data=df_long, x='Group', y='Value', order=group_order,
                  palette=palette, jitter=True, dodge=True, alpha=0.7,
                  legend=False, ax=ax, size=5) # Ajustar tamaño y alpha

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Grupos Comparados") # Etiqueta genérica para X
    plt.xticks(rotation=30, ha="right")
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 3. Añadir anotaciones estadísticas con Statannot
    if stats_results and 'p_value' in stats_results and len(group_order) >= 2:
        p_value = stats_results['p_value']
        test_name = stats_results.get('test_name', 'Test')

        # Definir pares de comparación (todos los pares posibles por ahora)
        box_pairs = [(group_order[i], group_order[j])
                     for i in range(len(group_order))
                     for j in range(i + 1, len(group_order))]

        if box_pairs:
            try:
                # Nota: statannot usualmente recalcula el test, pero podemos pasarle
                # p-valores precalculados si tuviéramos todos los pares.
                # Por ahora, le dejamos calcular (usará Mann-Whitney U por defecto
                # si no especificamos el test).
                # OJO: Esto puede ser inconsistente si el test original fue otro.
                # Una solución más robusta sería calcular todos los pares en
                # AnalysisService o usar una librería que haga post-hoc.
                # Por simplicidad visual ahora, solo mostramos la anotación
                # si el test principal fue significativo (p < 0.05) y
                # dejamos que statannot use Mann-Whitney U para los pares.
                # O, mejor aún, pasamos el p-valor principal si solo hay 2 grupos.

                if len(group_order) == 2:
                     # Si solo hay dos grupos, usar el p-valor calculado
                     custom_p_values = [p_value]
                     add_stat_annotation(ax, data=df_long, x='Group', y='Value',
                                         order=group_order,
                                         box_pairs=box_pairs,
                                         perform_stat_test=False, # No recalcular
                                         pvalues=custom_p_values,
                                         test=None, # No necesita test si damos pval
                                         text_format='star', # NS, *, **, ***, ****
                                         loc='inside', verbose=0)
                elif len(group_order) > 2:
                     # Para >2 grupos, dejamos que statannot haga Mann-Whitney U
                     # entre pares por ahora, ya que no tenemos post-hoc.
                     # Podríamos añadir una nota indicando esto.
                     add_stat_annotation(ax, data=df_long, x='Group', y='Value',
                                         order=group_order,
                                         box_pairs=box_pairs,
                                         test='Mann-Whitney', # Test por defecto
                                         text_format='star',
                                         loc='inside', verbose=0)
                     # Añadir nota sobre el test usado para anotaciones
                     plt.text(0.99, 0.01, 'Anotaciones: Mann-Whitney U (pares)',
                              verticalalignment='bottom', horizontalalignment='right',
                              transform=ax.transAxes, color='gray', fontsize=8)


            except Exception as e_annot:
                logger.error(f"Error añadiendo anotaciones estadísticas: {e_annot}")

    # 4. Añadir Leyenda (similar al ejemplo H Salto.png)
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
