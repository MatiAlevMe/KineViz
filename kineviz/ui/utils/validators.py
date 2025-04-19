import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# validate_study_data se movió al diálogo StudyDialog

def validate_filename_for_study_criteria(filename: str, vi_structure: list[dict]) -> tuple[bool, list[str | None] | None]:
    """
    Valida si un nombre de archivo cumple con la estructura de VIs definida.

    Formato esperado: PteXX [VI1_Desc] [VI2_Desc] ... [VIn_Desc] IntentoNN[_Frecuencia].ext
    Donde [VIk_Desc] es un descriptor válido para la k-ésima VI o la palabra "Nulo".

    :param filename: Nombre del archivo (con o sin extensión).
    :param vi_structure: Lista de diccionarios describiendo las VIs y sus descriptores.
                         Ej: [{'name': 'Tipo Salto', 'descriptors': ['CMJ', 'SJ']}, ...]
    :return: Tupla (bool, list[str | None] | None):
             - bool: True si el nombre es válido, False si no.
             - list: Lista con los descriptores encontrados en cada posición VI
                     (o None si se usó "Nulo"). None si la validación falla.
    """
    logger.debug(f"--- Validando nombre archivo: '{filename}' ---")
    logger.debug(f"Estructura VI: {vi_structure}")

    num_vis = len(vi_structure)
    if num_vis == 0:
        logger.debug("Estudio no tiene VIs definidas. Se requiere formato PteXX IntentoNN.")
        # Permitir solo PteXX NN si no hay VIs? O requerir siempre VIs?
        # Por ahora, asumimos que si no hay VIs, no se valida contra descriptores.
        # Requerimos formato PteXX NN
        name_without_ext = Path(filename).stem
        base_name_parts = name_without_ext.rsplit('_', 1)
        processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]
        if len(base_name_parts) == 2 and base_name_parts[1] in processed_folders:
            base_name = base_name_parts[0]
        else:
            base_name = name_without_ext

        parts = base_name.replace('_', ' ').split()
        if len(parts) == 2 and parts[0].lower().startswith('pte') and parts[1].isdigit():
             logger.debug("Validación Éxito (Sin VIs): Formato PteXX NN correcto.")
             return True, [] # Devolver lista vacía de descriptores
        else:
             logger.debug("Validación Fallo (Sin VIs): Formato no es PteXX NN.")
             return False, None


    # --- Lógica para estudios CON VIs definidas ---
    name_without_ext = Path(filename).stem
    base_name_parts = name_without_ext.rsplit('_', 1)
    processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]
    if len(base_name_parts) == 2 and base_name_parts[1] in processed_folders:
        base_name = base_name_parts[0]
    else:
        base_name = name_without_ext
        logger.debug(f"Validador: Nombre '{filename}' sin sufijo de frecuencia esperado. Usando '{base_name}'.")

    parts = base_name.replace('_', ' ').split()
    logger.debug(f"Partes base: {parts}")

    # Validar estructura general: PteXX + VIs + NN
    expected_parts = 1 + num_vis + 1
    if len(parts) != expected_parts:
        logger.debug(f"Fallo: Número incorrecto de partes. Esperado={expected_parts}, Obtenido={len(parts)}")
        return False, None

    # Validar PteXX
    if not parts[0].lower().startswith('pte'):
        logger.debug(f"Fallo: Primera parte '{parts[0]}' no empieza con 'pte'.")
        return False, None

    # Validar IntentoNN
    if not parts[-1].isdigit():
        logger.debug(f"Fallo: Última parte '{parts[-1]}' no es un número (IntentoNN).")
        return False, None

    # Validar descriptores intermedios
    parsed_descriptors = []
    found_non_nulo = False
    for i in range(num_vis):
        vi_index = i
        descriptor_part = parts[1 + i] # Parte correspondiente a esta VI
        allowed_descriptors = set(vi_structure[vi_index].get('descriptors', []))

        if descriptor_part == "Nulo":
            parsed_descriptors.append(None) # Usar None para representar "Nulo"
            logger.debug(f"VI {vi_index+1}: Encontrado 'Nulo'.")
        elif descriptor_part in allowed_descriptors:
            parsed_descriptors.append(descriptor_part)
            found_non_nulo = True
            logger.debug(f"VI {vi_index+1}: Encontrado descriptor válido '{descriptor_part}'.")
        else:
            logger.debug(f"Fallo: VI {vi_index+1}: Parte '{descriptor_part}' no es 'Nulo' ni un descriptor válido ({allowed_descriptors}).")
            return False, None

    # Validar regla: al menos un descriptor no debe ser "Nulo"
    if not found_non_nulo:
        logger.debug("Fallo: Todas las partes de VI son 'Nulo'. Se requiere al menos un descriptor válido.")
        return False, None

    # Si todas las validaciones pasan
    logger.debug(f"Validación Éxito. Descriptores parseados: {parsed_descriptors}")
    return True, parsed_descriptors
