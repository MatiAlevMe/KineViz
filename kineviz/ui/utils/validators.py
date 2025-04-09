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
    logger.debug(f"Validando nombre: '{filename}' con descriptores: {descriptors}")

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
        logger.debug("Validación fallida: No tiene al menos 2 partes.")
        return False

    # Verificar que la última parte antes de la frecuencia sea un número (NN)
    # y la primera parte empiece con 'Pte' (o similar identificador de paciente)
    # Esta validación es básica, podría mejorarse con regex.
    if not parts[-1].isdigit() or not parts[0].lower().startswith('pte'):
         logger.debug(f"Validación fallida: No cumple patrón Pte...NN (Inicio: '{parts[0]}', Fin: '{parts[-1]}')")
         # Podríamos ser más estrictos con el formato del paciente si es necesario
         return False

    # Si no hay descriptores definidos para el estudio, solo validamos PteXX NN
    if not descriptors:
        is_valid = len(parts) == 2
        logger.debug(f"Validación (sin descriptores definidos): {'Éxito' if is_valid else 'Fallo'} (Se esperaban 2 partes).")
        return is_valid

    # Si hay descriptores definidos para el estudio:
    if descriptors:
        valid_descriptors_set = set(descriptors)
        intermediate_parts = parts[1:-1] # Partes entre PteXX y NN

        logger.debug(f"Descriptores definidos: {descriptors}")
        valid_descriptors_set = set(descriptors)
        intermediate_parts = parts[1:-1] # Partes entre PteXX y NN
        logger.debug(f"Partes intermedias encontradas: {intermediate_parts}")

        # 1. Debe haber al menos una parte intermedia si hay descriptores definidos
        if not intermediate_parts:
            logger.debug("Validación fallida: Se definieron descriptores pero no se encontraron partes intermedias.")
            return False

        # 2. Todas las partes intermedias deben ser descriptores válidos definidos para el estudio
        invalid_parts = [part for part in intermediate_parts if part not in valid_descriptors_set]
        if invalid_parts:
            logger.debug(f"Validación fallida: Partes intermedias inválidas encontradas: {invalid_parts}")
            return False

        # 3. Las partes intermedias deben mantener el orden relativo definido en 'descriptors'
        #    Permitiendo omitir descriptores.
        last_index_in_definition = -1 # Índice en 'descriptors' del descriptor anterior encontrado en el nombre
        for part_in_filename in intermediate_parts:
            try:
                # Encontrar dónde está definido este descriptor
                current_index_in_definition = descriptors.index(part_in_filename)
                logger.debug(f"Parte '{part_in_filename}' encontrada en índice {current_index_in_definition} de descriptores definidos.")

                # Comprobar si el índice de definición actual es estrictamente mayor
                # que el índice de definición del descriptor anterior encontrado en el nombre.
                if current_index_in_definition > last_index_in_definition:
                    # El orden es correcto hasta ahora, actualizar el último índice encontrado
                    last_index_in_definition = current_index_in_definition
                else:
                    # Error de orden: este descriptor aparece antes en la definición
                    # que el descriptor anterior encontrado en el nombre.
                    logger.debug(f"Validación fallida: Error de orden relativo. '{part_in_filename}' (índice {current_index_in_definition}) no está después del último descriptor encontrado previamente (índice {last_index_in_definition}).")
                    return False

            except ValueError:
                # Este caso no debería ocurrir si la comprobación #2 (invalid_parts) funcionó.
                logger.error(f"Error inesperado: Descriptor '{part_in_filename}' no encontrado en lista original {descriptors} durante chequeo de orden.")
                return False

        # Si todas las comprobaciones pasan
        logger.debug("Validación exitosa: Cumple formato y descriptores (incluyendo orden).")
        return True
    # else: # Este else ya no es necesario debido a la estructura if/if/else anterior
    #     # Si no hay descriptores definidos para el estudio, solo validamos PteXX NN
    #     is_valid = len(parts) == 2
    #     logger.debug(f"Validación (sin descriptores definidos): {'Éxito' if is_valid else 'Fallo'} (Se esperaban 2 partes).")
    #     return is_valid
