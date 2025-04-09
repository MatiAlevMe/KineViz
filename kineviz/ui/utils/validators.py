import logging # Importar logging

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
    logger = logging.getLogger(__name__) # Asegurar logger
    # Log inicial para confirmar entrada y argumentos
    logger.debug(f"--- ENTERING validate_filename_for_study_criteria ---")
    logger.debug(f"Input filename: '{filename}'")
    logger.debug(f"Input descriptors: {descriptors}")

    # --- Lógica mejorada para extraer base_name ---
    # No omitir validación basada solo en sufijo de frecuencia.
    # La validación se basa en el patrón Pte...NN y los descriptores.
    # Los archivos OG u otros se filtrarán antes si es necesario.

    # Importar Path dentro de la función o al inicio del archivo si no está ya
    from pathlib import Path
    # Eliminar import logging redundante de aquí
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
    logger.debug(f"Base name extraído: '{base_name}'")
    # --- Fin lógica mejorada ---

    parts = base_name.replace('_', ' ').split() # Dividir por espacios y guiones bajos convertidos
    logger.debug(f"Partes del nombre base: {parts}")

    # Se espera al menos PteXX y NN (2 partes)
    if len(parts) < 2:
        logger.debug("Validation Failed: Less than 2 parts after splitting base name.")
        return False

    # Verificar que la última parte antes de la frecuencia sea un número (NN)
    # y la primera parte empiece con 'Pte' (o similar identificador de paciente)
    # Esta validación es básica, podría mejorarse con regex.
    last_part_is_digit = parts[-1].isdigit()
    first_part_starts_pte = parts[0].lower().startswith('pte')
    if not last_part_is_digit or not first_part_starts_pte:
         logger.debug(f"Validation Failed: Doesn't match Pte...NN pattern. Start: '{parts[0]}' (Starts 'pte'? {first_part_starts_pte}), End: '{parts[-1]}' (Is digit? {last_part_is_digit})")
         return False

    # Si no hay descriptores definidos para el estudio, solo validamos PteXX NN
    if not descriptors:
        is_valid = len(parts) == 2
        logger.debug(f"Validación (sin descriptores definidos): {'Éxito' if is_valid else 'Fallo'} (Se esperaban 2 partes).")
        return is_valid

    # Si hay descriptores definidos para el estudio:
    if descriptors:
        logger.debug("Processing descriptors...")
        valid_descriptors_set = set(descriptors)
        intermediate_parts = parts[1:-1] # Partes entre PteXX y NN
        logger.debug(f"Intermediate parts found: {intermediate_parts}")

        # 1. Si hay descriptores definidos, debe haber partes intermedias O NINGUNA.
        #    Si hay partes intermedias, deben ser validadas.
        #    Si NO hay partes intermedias, el nombre es inválido si se definieron descriptores.
        if not intermediate_parts:
             logger.debug("Validation Failed: Descriptors defined, but no intermediate parts found in filename.")
             return False

        # 2. Todas las partes intermedias deben ser descriptores válidos definidos para el estudio
        invalid_parts = [part for part in intermediate_parts if part not in valid_descriptors_set]
        if invalid_parts:
            logger.debug(f"Validation Failed: Invalid intermediate parts found: {invalid_parts}")
            return False

        # 3. Las partes intermedias deben ser un subconjunto ordenado de los descriptores definidos
        last_found_descriptor_index = -1 # Índice en 'descriptors' del último descriptor encontrado en el nombre del archivo
        for part in intermediate_parts:
            try:
                # Loggear antes de buscar el índice
                logger.debug(f"Buscando índice para parte: '{part}' (len={len(part)}) en descriptores definidos: {descriptors}")
                # Encontrar el índice de la parte actual en la lista de descriptores definidos
                current_index_in_definition = descriptors.index(part)
                logger.debug(f"Parte '{part}' encontrada en índice {current_index_in_definition} de descriptores definidos.")

                # Verificar si el índice actual es mayor que el índice del descriptor anterior encontrado
                if current_index_in_definition > last_found_descriptor_index:
                    # El orden es correcto hasta ahora, actualizar el último índice encontrado
                    last_found_descriptor_index = current_index_in_definition
                else:
                    # Error de orden: este descriptor aparece antes o en el mismo lugar que el anterior
                    logger.debug(f"Validation Failed: Relative order error. '{part}' (index {current_index_in_definition}) is not after the last found descriptor (index {last_found_descriptor_index}).")
                    return False

            except ValueError:
                # Si 'part' no está en 'descriptors', el nombre de archivo es inválido
                logger.debug(f"Validation Failed: Descriptor '{part}' not found in defined list: {descriptors}")
                return False

        # Si todas las partes intermedias son válidas y están en el orden correcto
        logger.debug("Validación de descriptores exitosa: Cumple formato y orden.")
        return True
    # else: # Este else ya no es necesario debido a la estructura if/if/else anterior
    #     # Si no hay descriptores definidos para el estudio, solo validamos PteXX NN
    #     is_valid = len(parts) == 2
    #     logger.debug(f"Validación (sin descriptores definidos): {'Éxito' if is_valid else 'Fallo'} (Se esperaban 2 partes).")
    #     return is_valid
