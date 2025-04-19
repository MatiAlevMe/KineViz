import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional # Para type hints

logger = logging.getLogger(__name__) # Logger para este módulo

# --- NUEVO VALIDADOR DE DATOS DE ESTUDIO (VI) ---
def validate_study_iv_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Valida los datos de un estudio con estructura de Variables Independientes (VI).

    :param data: Diccionario con datos del estudio, incluyendo 'independent_variables'
                 como lista de diccionarios [{'name': str, 'descriptors': [str]}].
    :return: Tupla (bool, str or None) indicando validez y mensaje de error.
    """
    # 1. Validar campos básicos (nombre, sujetos, intentos)
    name = data.get('name', '').strip()
    if not name:
        return False, "El nombre del estudio es obligatorio."
    if len(name) < 3:
        return False, "El nombre del estudio debe tener al menos 3 caracteres."

    num_subjects_str = data.get('num_subjects', '')
    if not num_subjects_str:
         return False, "El número de sujetos es obligatorio."
    try:
        num_subjects = int(num_subjects_str)
        if num_subjects <= 0:
            return False, "El número de sujetos debe ser un entero positivo."
    except ValueError:
        return False, "El número de sujetos debe ser un número entero."

    attempts_count_str = data.get('attempts_count', '')
    if not attempts_count_str:
        return False, "La cantidad de intentos es obligatoria."
    try:
        attempts = int(attempts_count_str)
        if attempts <= 0:
            return False, "La cantidad de intentos debe ser un entero positivo."
    except ValueError:
        return False, "La cantidad de intentos debe ser un número entero."

    # 2. Validar estructura de Variables Independientes
    independent_variables = data.get('independent_variables', [])
    if not isinstance(independent_variables, list):
        return False, "La estructura de Variables Independientes es inválida."

    if not independent_variables:
        return False, "Debe definir al menos una Variable Independiente."

    all_vi_names = set()
    all_descriptor_names = set()

    for i, iv in enumerate(independent_variables):
        if not isinstance(iv, dict):
            return False, f"Formato inválido para Variable Independiente #{i+1}."

        # Validar nombre de VI
        vi_name = iv.get('name', '').strip()
        if not vi_name:
            return False, f"El nombre de la Variable Independiente #{i+1} no puede estar vacío."
        if vi_name in all_vi_names:
            return False, f"Nombre de Variable Independiente duplicado: '{vi_name}'."
        all_vi_names.add(vi_name)

        # Validar descriptores de VI
        descriptors = iv.get('descriptors', [])
        if not isinstance(descriptors, list):
            return False, f"Los descriptores para '{vi_name}' deben ser una lista."
        if len(descriptors) < 2:
            return False, f"La Variable Independiente '{vi_name}' debe tener al menos dos descriptores."

        cleaned_descriptors_in_iv = set()
        for j, desc in enumerate(descriptors):
            if not isinstance(desc, str):
                 return False, f"Descriptor inválido (no es texto) en '{vi_name}'."
            cleaned_desc = desc.strip()
            if not cleaned_desc:
                return False, f"Descriptor vacío encontrado en '{vi_name}'."
            if ' ' in cleaned_desc:
                return False, f"El descriptor '{cleaned_desc}' en '{vi_name}' no puede contener espacios."
            # Añadir validación para no permitir "Nulo" (case-insensitive)
            if cleaned_desc.lower() == "nulo":
                return False, f"El descriptor '{cleaned_desc}' en '{vi_name}' no puede llamarse 'Nulo'."
            if cleaned_desc in cleaned_descriptors_in_iv:
                return False, f"Descriptor duplicado '{cleaned_desc}' dentro de la Variable Independiente '{vi_name}'."
            if cleaned_desc in all_descriptor_names:
                return False, f"Descriptor duplicado '{cleaned_desc}' encontrado en múltiples Variables Independientes."

            cleaned_descriptors_in_iv.add(cleaned_desc)
            all_descriptor_names.add(cleaned_desc)

    # Si todas las validaciones pasan
    return True, None


# --- VALIDADOR DE NOMBRE DE ARCHIVO REFACTORIZADO ---
def validate_filename_for_study_criteria(
    filename: str,
    independent_variables: List[Dict[str, Any]]
) -> Tuple[bool, List[Optional[str]]]:
    """
    Valida si un nombre de archivo cumple con la estructura de VIs del estudio.

    Formato esperado: PteXX [VAL_VI1] [VAL_VI2] ... [VAL_VIn] NN[_Frecuencia].ext
    Permite 'Nulo' como valor. Verifica orden y pertenencia a descriptores de cada VI.

    :param filename: Nombre del archivo (sin ruta, solo nombre base con extensión).
    :param independent_variables: Lista de VIs definidas para el estudio
                                  (ej: [{'name': 'Tipo', 'descriptors': ['A', 'B']}]).
    :return: Tupla (bool, list[str|None]).
             - Si es válido: (True, lista de descriptores extraídos o None si era 'Nulo').
             - Si es inválido: (False, []).
    """
    logger.debug(f"--- Validando nombre archivo: '{filename}' ---")
    logger.debug(f"VIs definidas: {independent_variables}")

    # 1. Extraer nombre base (sin extensión ni frecuencia)
    name_without_ext = Path(filename).stem
    processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]
    base_name_parts = name_without_ext.rsplit('_', 1)
    if len(base_name_parts) == 2 and base_name_parts[1] in processed_folders:
        base_name = base_name_parts[0]
    else:
        base_name = name_without_ext
    logger.debug(f"Nombre base extraído: '{base_name}'")

    # 2. Dividir nombre base por espacios
    parts = base_name.split()
    logger.debug(f"Partes del nombre base: {parts}")

    # 3. Validaciones básicas de estructura
    if len(parts) < 2:
        logger.debug("Fallo: Menos de 2 partes (se espera PteXX y NN).")
        return False, []
    if not parts[0].lower().startswith('pte'):
        logger.debug(f"Fallo: Primera parte '{parts[0]}' no empieza con 'pte'.")
        return False, []
    if not parts[-1].isdigit():
        logger.debug(f"Fallo: Última parte '{parts[-1]}' no es un número (NN).")
        return False, []

    # 4. Extraer partes intermedias (potenciales descriptores)
    intermediate_parts = parts[1:-1]
    num_vis_defined = len(independent_variables)
    num_intermediate = len(intermediate_parts)
    logger.debug(f"Partes intermedias (descriptores): {intermediate_parts}")
    logger.debug(f"Número VIs definidas: {num_vis_defined}, Partes intermedias encontradas: {num_intermediate}")

    # 5. Validar número de partes intermedias vs VIs definidas
    if num_intermediate != num_vis_defined:
        logger.debug(f"Fallo: Número de partes intermedias ({num_intermediate}) no coincide con VIs definidas ({num_vis_defined}).")
        return False, []

    # 6. Validar cada parte intermedia
    extracted_descriptors: List[Optional[str]] = []
    has_non_nulo_descriptor = False
    for i, part in enumerate(intermediate_parts):
        vi_definition = independent_variables[i]
        valid_descriptors_for_vi = set(vi_definition.get('descriptors', []))

        if part == "Nulo":
            extracted_descriptors.append(None) # Usar None para representar 'Nulo' internamente
            logger.debug(f"Parte {i+1}: '{part}' es Nulo.")
        elif part in valid_descriptors_for_vi:
            extracted_descriptors.append(part)
            has_non_nulo_descriptor = True
            logger.debug(f"Parte {i+1}: '{part}' es válido para VI '{vi_definition.get('name', 'N/A')}'.")
        else:
            logger.debug(f"Fallo: Parte {i+1} '{part}' no es 'Nulo' ni un descriptor válido para VI '{vi_definition.get('name', 'N/A')}' ({valid_descriptors_for_vi}).")
            return False, []

    # 7. Validar que al menos un descriptor no sea "Nulo"
    if not has_non_nulo_descriptor and num_vis_defined > 0: # Solo aplicar si hay VIs definidas
        logger.debug("Fallo: Todas las partes intermedias son 'Nulo'. Se requiere al menos un descriptor válido.")
        return False, []

    # 8. Si todas las validaciones pasan
    logger.debug(f"Validación exitosa. Descriptores extraídos: {extracted_descriptors}")
    return True, extracted_descriptors


# --- ELIMINAR VALIDADOR ANTIGUO ---
# La función validate_study_data ya no es necesaria y se elimina.
