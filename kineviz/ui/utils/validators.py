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

    # Validar Descriptores (lista de strings pasada desde el diálogo)
    descriptors = data.get('descriptores', [])
    cleaned_descriptors = [d.strip() for d in descriptors if d.strip()] # Limpiar y quitar vacíos

    # Verificar duplicados exactos (sensible a mayúsculas/minúsculas)
    if len(cleaned_descriptors) != len(set(cleaned_descriptors)):
        # Encontrar los duplicados para el mensaje de error
        counts = {}
        duplicates = set()
        for d in cleaned_descriptors:
            counts[d] = counts.get(d, 0) + 1
            if counts[d] > 1:
                duplicates.add(d)
        return False, f"Los siguientes descriptores están duplicados: {', '.join(duplicates)}"

    # Si todas las validaciones pasan
    return True, None


def validate_filename_for_study_criteria(filename: str, descriptors: list[str]) -> bool:
    """
    Valida si un nombre de archivo cumple con los criterios de descriptores del estudio.

    Asume un formato como: PteXX [DESC1] [DESC2] ... NN_Frecuencia.ext
    Donde [DESCn] son los descriptores definidos para el estudio.
    Verifica que las partes intermedias correspondan a descriptores válidos.

    :param filename: El nombre del archivo (sin ruta, solo el nombre base con extensión).
    :param descriptors: Lista de descriptores válidos para el estudio.
    :return: True si el nombre de archivo es válido según los criterios, False en caso contrario.
    """
    # Ignorar archivos que no parecen seguir el formato esperado (ej. reportes, archivos temporales, etc.)
    # o archivos dentro de la carpeta OG que no deben ser validados por criterios.
    # Una heurística simple es verificar si contiene los sufijos de frecuencia.
    if not any(freq in filename for freq in ["_Cinematica", "_Cinetica", "_Electromiografica"]):
        # Podríamos refinar esto, pero por ahora asumimos que solo validamos archivos procesados.
        # O podríamos pasar el tipo de archivo ('Processed', 'Original') y solo validar 'Processed'.
        # Devolvemos True aquí para no bloquear archivos OG u otros que no necesiten validación de descriptores.
        return True

    # --- Lógica mejorada para extraer base_name ---
    # Importar Path dentro de la función o al inicio del archivo si no está ya
    from pathlib import Path
    import logging # Asegurar que logging esté importado
    logger = logging.getLogger(__name__) # Obtener logger si no está a nivel de módulo

    # 1. Quitar extensión
    name_without_ext = Path(filename).stem
    # 2. Quitar sufijo de frecuencia (_Cinematica, etc.) usando rsplit
    base_name_parts = name_without_ext.rsplit('_', 1)
    # Verificar si el split funcionó y si la última parte es una frecuencia conocida
    processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]
    if len(base_name_parts) == 2 and base_name_parts[1] in processed_folders:
        base_name = base_name_parts[0]
    else:
        # Si no hay sufijo de frecuencia o no es conocido, usar el nombre sin extensión
        base_name = name_without_ext
        # Si no tiene sufijo de frecuencia, no debería validarse contra descriptores?
        # Por ahora, continuamos la validación con base_name, pero esto podría necesitar ajuste.
        logger.debug(f"Validador: Nombre de archivo '{filename}' no parece tener sufijo de frecuencia esperado. Usando '{base_name}' como base para validación de descriptores.")
    # --- Fin lógica mejorada ---

    parts = base_name.replace('_', ' ').split() # Dividir por espacios y guiones bajos convertidos

    # Se espera al menos PteXX y NN (2 partes)
    if len(parts) < 2:
        return False

    # Verificar que la última parte antes de la frecuencia sea un número (NN)
    # y la primera parte empiece con 'Pte' (o similar identificador de paciente)
    # Esta validación es básica, podría mejorarse con regex.
    if not parts[-1].isdigit() or not parts[0].lower().startswith('pte'):
         # Podríamos ser más estrictos con el formato del paciente si es necesario
         return False

    # Si no hay descriptores definidos para el estudio, solo validamos PteXX NN
    if not descriptors:
        return len(parts) == 2

    # Si hay descriptores definidos para el estudio:
    if descriptors:
        valid_descriptors_set = set(descriptors)
        intermediate_parts = parts[1:-1] # Partes entre PteXX y NN

        # 1. Debe haber al menos una parte intermedia si hay descriptores definidos
        if not intermediate_parts:
            return False

        # 2. Todas las partes intermedias deben ser descriptores válidos definidos para el estudio
        if not all(part in valid_descriptors_set for part in intermediate_parts):
            return False

        # 3. Las partes intermedias deben mantener el orden relativo definido en 'descriptors'
        last_index = -1
        for part in intermediate_parts:
            try:
                # Encontrar el índice de esta parte en la lista original de descriptores (que mantiene el orden)
                current_index = descriptors.index(part)
                # Verificar si el índice actual es mayor que el anterior
                if current_index <= last_index:
                    return False # Error de orden
                last_index = current_index
            except ValueError:
                 # Esto no debería ocurrir si la comprobación anterior (all) funcionó, pero por seguridad:
                 return False # Descriptor no encontrado en la lista original

        # Si todas las comprobaciones pasan
        return True
    else:
        # Si no hay descriptores definidos para el estudio, solo validamos PteXX NN
        return len(parts) == 2
