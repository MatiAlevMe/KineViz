def validate_study_data(data):
    """
    Valida los datos de un estudio.

    :param data: Diccionario con datos del estudio.
    :return: Tupla (bool, str or None) indicando si los datos son válidos y un mensaje de error si no lo son.
    """
    # Validar nombre
    name = data.get('name', '').strip()
    if not name:
        return False, "El nombre del estudio es obligatorio."
    if len(name) < 3:
        return False, "El nombre del estudio debe tener al menos 3 caracteres."

    # Validar número de sujetos
    num_subjects_str = data.get('num_subjects', '')
    if not num_subjects_str:
         return False, "El número de sujetos es obligatorio."
    try:
        num_subjects = int(num_subjects_str)
        if num_subjects <= 0:
            return False, "El número de sujetos debe ser un entero positivo."
    except ValueError:
        return False, "El número de sujetos debe ser un número entero."

    # Validar tipos de prueba (opcional, pero si se provee, no debe estar vacío)
    # test_types = data.get('test_types', '').strip()
    # if not test_types:
    #     return False, "Debe especificar al menos un tipo de prueba."
    # Permitir que tipos y periodos estén vacíos, pero validar duplicados si ambos existen

    # Validar periodos de prueba (opcional, pero si se provee, no debe estar vacío)
    # test_periods = data.get('test_periods', '').strip()
    # if not test_periods:
    #     return False, "Debe especificar al menos un periodo de prueba."

    # Validar cantidad de intentos
    attempts_count_str = data.get('attempts_count', '')
    if not attempts_count_str:
        return False, "La cantidad de intentos es obligatoria."
    try:
        attempts = int(attempts_count_str)
        if attempts <= 0:
            return False, "La cantidad de intentos debe ser un entero positivo."
    except ValueError:
        return False, "La cantidad de intentos debe ser un número entero."

    # Validar que no haya valores duplicados entre tipos y periodos de prueba (después de limpiar)
    tipos_prueba_str = data.get('test_types', '')
    periodos_prueba_str = data.get('test_periods', '')

    # Limpiar y filtrar valores vacíos antes de la validación de duplicados
    tipos_prueba = {t.strip() for t in tipos_prueba_str.split(',') if t.strip()}
    periodos_prueba = {p.strip() for p in periodos_prueba_str.split(',') if p.strip()}

    # Solo realizar la comprobación de duplicados si ambos conjuntos tienen elementos después de limpiar
    if tipos_prueba and periodos_prueba:
        duplicates = tipos_prueba.intersection(periodos_prueba)
        if duplicates:
            return False, f"Los siguientes valores están duplicados entre Tipos y Periodos de prueba: {', '.join(duplicates)}"

    # Si todas las validaciones pasan
    return True, None


def validate_filename_for_study_criteria(filename: str, test_types: list[str], test_periods: list[str]) -> bool:
    """
    Valida si un nombre de archivo cumple con los criterios de tipos y periodos de prueba.

    :param filename: El nombre del archivo (sin ruta, solo el nombre base con extensión).
    :param test_types: Lista de tipos de prueba válidos para el estudio.
    :param test_periods: Lista de periodos de prueba válidos para el estudio.
    :return: True si el nombre de archivo es válido según los criterios, False en caso contrario.
    """
    # Ignorar archivos que no parecen seguir el formato esperado (ej. reportes, archivos temporales)
    # O archivos dentro de la carpeta OG que no deben ser validados por criterios.
    # Una heurística simple es verificar si contiene los sufijos de frecuencia.
    if not any(freq in filename for freq in ["_Cinematica", "_Cinetica", "_Electromiografica"]):
        # Podríamos refinar esto, pero por ahora asumimos que solo validamos archivos procesados.
        # O podríamos pasar el tipo de archivo ('Processed', 'Original') y solo validar 'Processed'.
        return True # No validar archivos no procesados o con nombres inesperados

    # Extraer el nombre base sin el sufijo de frecuencia y extensión
    name_parts = filename.split('_')
    if len(name_parts) < 2: # No tiene sufijo de frecuencia
        base_name = filename.split('.')[0]
    else:
        base_name = '_'.join(name_parts[:-1]) # Unir todo excepto el último elemento (frecuencia)
        base_name = base_name.split('.')[0] # Quitar extensión si aún está

    parts = base_name.replace('_', ' ').split() # Dividir por espacios

    # Limpiar listas de criterios (quitar vacíos)
    valid_types = {t for t in test_types if t}
    valid_periods = {p for p in test_periods if p}

    # --- Lógica de validación basada en interfaz.py ---
    # Caso 1: Sin tipos ni periodos definidos -> formato "PteXX NN" (2 partes)
    if not valid_types and not valid_periods:
        return len(parts) == 2

    # Caso 2: Solo tipos o solo periodos definidos -> formato "PteXX CRITERIO NN" (3 partes)
    if bool(valid_types) != bool(valid_periods): # XOR
        if len(parts) != 3:
            return False
        middle_part = parts[1]
        if valid_types:
            return middle_part in valid_types
        else: # Solo periodos
            return middle_part in valid_periods

    # Caso 3: Ambos tipos y periodos definidos -> formato "PteXX TIPO PERIODO NN" o "PteXX PERIODO TIPO NN" (4 partes)
    if len(parts) != 4:
        return False
    # Verificar ambas combinaciones posibles
    order1_valid = (parts[1] in valid_types and parts[2] in valid_periods)
    order2_valid = (parts[1] in valid_periods and parts[2] in valid_types)
    return order1_valid or order2_valid
