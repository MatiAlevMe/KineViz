import logging
import re # Importar re para expresiones regulares
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Set # Para type hints

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
    # Sub-valor names can be duplicated across different VIs, but not within the same VI.
    # We don't need all_descriptor_names at the top level for this validation.

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

        # Validar sub-valores de VI
        descriptors = iv.get('descriptors', [])
        if not isinstance(descriptors, list):
            return False, f"Los sub-valores para '{vi_name}' deben ser una lista."
        if len(descriptors) < 2:
            return False, f"La Variable Independiente '{vi_name}' debe tener al menos dos sub-valores."

        cleaned_descriptors_in_iv = set()
        for j, desc in enumerate(descriptors):
            if not isinstance(desc, str):
                 return False, f"Sub-valor inválido (no es texto) en '{vi_name}'."
            cleaned_desc = desc.strip()
            if not cleaned_desc:
                return False, f"Sub-valor vacío encontrado en '{vi_name}'."
            if ' ' in cleaned_desc:
                return False, f"El sub-valor '{cleaned_desc}' en '{vi_name}' no puede contener espacios."
            # Añadir validación para no permitir "Nulo" (case-insensitive)
            if cleaned_desc.lower() == "nulo":
                return False, f"El sub-valor '{cleaned_desc}' en '{vi_name}' no puede llamarse 'Nulo'."
            if cleaned_desc in cleaned_descriptors_in_iv:
                return False, f"Sub-valor duplicado '{cleaned_desc}' dentro de la Variable Independiente '{vi_name}'."
            # No es un error tener el mismo nombre de sub-valor en diferentes VIs.
            # if cleaned_desc in all_descriptor_names:
            #     return False, f"Sub-valor duplicado '{cleaned_desc}' encontrado en múltiples Variables Independientes."

            cleaned_descriptors_in_iv.add(cleaned_desc)
            # all_descriptor_names.add(cleaned_desc) # No es necesario para la validación actual

        # Validar flags de la VI
        allows_combination = iv.get('allows_combination', False)
        is_mandatory = iv.get('is_mandatory', False)

        if not isinstance(allows_combination, bool):
            return False, f"El valor de 'Permite combinación' para la VI '{vi_name}' debe ser verdadero o falso."
        if not isinstance(is_mandatory, bool):
            return False, f"El valor de 'Obligatorio' para la VI '{vi_name}' debe ser verdadero o falso."

        if is_mandatory and not allows_combination:
            return False, f"Para la VI '{vi_name}', 'Obligatorio' solo puede ser verdadero si 'Permite combinación' también lo es."

    # Si todas las validaciones pasan
    return True, None


# --- VALIDADOR DE NOMBRE DE ARCHIVO REFACTORIZADO ---
def validate_filename_for_study_criteria(
    filename: str,
    independent_variables: List[Dict[str, Any]]
) -> Tuple[bool, Optional[str], List[Optional[str]], Optional[int]]:
    """
    Valida si un nombre de archivo cumple con la estructura de VIs del estudio
    y extrae el ID del sujeto, los sub-valores y el número de intento.

    Formato esperado: [ID_Participante] [VAL_VI1] [VAL_VI2] ... [VAL_VIn] NN[_TipoDeDato].ext
    Donde [ID_Participante] es una combinación de letras seguidas de números (ej: P01, Sujeto007).
    Permite 'Nulo' como valor para VAL_VI. Verifica orden y pertenencia a sub-valores de cada VI.

    :param filename: Nombre del archivo (sin ruta, solo nombre base con extensión).
    :param independent_variables: Lista de VIs definidas para el estudio
                                  (ej: [{'name': 'Tipo', 'descriptors': ['A', 'B']}]).
    :return: Tupla (bool, subject_id|None, list[str|None], attempt_num|None).
             - Si es válido: (True, "ID_Participante", lista_sub-valores, NN).
             - Si es inválido: (False, None, [], None).
    """
    logger.debug(f"--- Validando nombre archivo: '{filename}' ---")
    logger.debug(f"VIs definidas: {independent_variables}")
    invalid_return = (False, None, [], None) # Valor de retorno para inválido

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

    # 3. Validaciones básicas de estructura y extracción de PteXX y NN
    if len(parts) < 2:
        logger.debug("Fallo: Menos de 2 partes (se espera ID_Participante y NN).")
        return invalid_return

    subject_id_part = parts[0]
    # Validar formato "Texto+Numero" para ID de participante (e.g., P01, Sujeto007)
    # Debe consistir en una o más letras seguidas de uno o más números.
    if not re.match(r"^[a-zA-Z]+[0-9]+$", subject_id_part):
        logger.debug(f"Fallo: Primera parte '{subject_id_part}' no sigue el formato 'Texto+Numero' (ej: P01, Sujeto007).")
        return invalid_return
    subject_id = subject_id_part # Guardar el ID_Participante extraído

    attempt_num_part = parts[-1]
    if not attempt_num_part.isdigit():
        logger.debug(f"Fallo: Última parte '{attempt_num_part}' no es un número (NN).")
        return invalid_return
    try:
        attempt_num = int(attempt_num_part)
        if attempt_num <= 0:
             logger.debug(f"Fallo: Número de intento '{attempt_num}' no es positivo.")
             return invalid_return
    except ValueError:
         logger.debug(f"Fallo: No se pudo convertir la última parte '{attempt_num_part}' a número de intento.")
         return invalid_return

    # 4. Extraer partes intermedias (potenciales sub-valores)
    intermediate_parts = parts[1:-1] # Entre PteXX y NN
    num_vis_defined = len(independent_variables)
    num_intermediate = len(intermediate_parts)
    logger.debug(f"Partes intermedias (sub-valores): {intermediate_parts}")
    logger.debug(f"Número VIs definidas: {num_vis_defined}, Partes intermedias encontradas: {num_intermediate}")

    # 5. Validar número de partes intermedias vs VIs definidas
    if num_intermediate != num_vis_defined:
        logger.debug(f"Fallo: Número de partes intermedias ({num_intermediate}) no coincide con VIs definidas ({num_vis_defined}).")
        return invalid_return

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
            logger.debug(f"Fallo: Parte {i+1} '{part}' no es 'Nulo' ni un sub-valor válido para VI '{vi_definition.get('name', 'N/A')}' ({valid_descriptors_for_vi}).")
            return invalid_return

    # 7. Validar que al menos un sub-valor no sea "Nulo"
    if not has_non_nulo_descriptor and num_vis_defined > 0: # Solo aplicar si hay VIs definidas
        logger.debug("Fallo: Todas las partes intermedias son 'Nulo'. Se requiere al menos un sub-valor válido.")
        return invalid_return

    # 8. Si todas las validaciones pasan
    logger.debug(f"Validación exitosa. Sujeto: {subject_id}, Sub-valores: {extracted_descriptors}, Intento: {attempt_num}")
    return True, subject_id, extracted_descriptors, attempt_num


# --- ELIMINAR VALIDADOR ANTIGUO ---
# La función validate_study_data ya no es necesaria y se elimina.


# --- NUEVO VALIDADOR DE REGLAS DE VI PARA LOTES DE ARCHIVOS ---
def validate_files_for_vi_rules(
    files_to_add_info: List[Dict[str, Any]],
    existing_files_descriptors: Dict[str, List[List[Optional[str]]]],
    independent_variables: List[Dict[str, Any]]
) -> List[str]:
    """
    Valida un lote de archivos a agregar contra las reglas de VI de un estudio,
    considerando los archivos ya existentes.

    :param files_to_add_info: Lista de diccionarios para archivos a agregar.
                              Cada dict debe tener: {'subject_id': str, 'descriptors': List[Optional[str]], 'filename': str}.
    :param existing_files_descriptors: Dict mapeando subject_id a una lista de sus listas de sub-valores existentes.
                                       Ej: {"Pte01": [["CMJ", "PRE"], ["SJ", "PRE"]]}
    :param independent_variables: Lista de definiciones de VIs del estudio.
    :return: Lista de mensajes de error. Lista vacía si es válido.
    """
    error_messages = []
    if not independent_variables: # No VIs, no rules to check beyond basic filename structure
        return []

    # Combine existing files with new files for a complete view per patient
    all_files_by_patient: Dict[str, List[List[Optional[str]]]] = {}

    # 1. Populate with existing files
    for subject_id, desc_lists in existing_files_descriptors.items():
        if subject_id not in all_files_by_patient:
            all_files_by_patient[subject_id] = []
        all_files_by_patient[subject_id].extend(desc_lists)

    # 2. Add new files to the structure
    all_patient_ids_in_study = set(all_files_by_patient.keys())
    for file_info in files_to_add_info:
        subject_id = file_info['subject_id']
        descriptors = file_info['descriptors']
        all_patient_ids_in_study.add(subject_id)
        if subject_id not in all_files_by_patient:
            all_files_by_patient[subject_id] = []
        all_files_by_patient[subject_id].append(descriptors)

    # 3. Validate against VI rules for each patient and each VI
    for vi_idx, vi_def in enumerate(independent_variables):
        vi_name = vi_def.get('name', f"VI #{vi_idx+1}")
        allows_combination = vi_def.get('allows_combination', False)
        is_mandatory = vi_def.get('is_mandatory', False)
        vi_defined_descriptors = set(d for d in vi_def.get('descriptors', []) if d) # Excluye None/empty

        for patient_id in sorted(list(all_patient_ids_in_study)):
            patient_files_descriptors = all_files_by_patient.get(patient_id, [])
            if not patient_files_descriptors: # No files for this patient (should not happen if they are in all_patient_ids_in_study from new files)
                continue

            # Get all descriptors used by this patient for the current VI
            descriptors_used_by_patient_for_vi: Set[Optional[str]] = set()
            for file_desc_list in patient_files_descriptors:
                if vi_idx < len(file_desc_list):
                    descriptors_used_by_patient_for_vi.add(file_desc_list[vi_idx])
                # else: sub-valor list shorter than VI index, implies "Nulo" or malformed filename already caught

            # Rule 1: Fixed Sub-valor (allows_combination == False)
            if not allows_combination:
                non_nulo_descriptors = {d for d in descriptors_used_by_patient_for_vi if d is not None}
                if len(non_nulo_descriptors) > 1:
                    error_messages.append(
                        f"Participante '{patient_id}': Para la VI '{vi_name}' (no permite combinación), "
                        f"se encontraron múltiples sub-valores diferentes: {', '.join(sorted(list(non_nulo_descriptors)))}. "
                        f"Solo se permite un sub-valor (o 'Nulo') por participante para esta VI."
                    )
            
            # Rule 2: Mandatory Sub-valor (allows_combination == True AND is_mandatory == True)
            if allows_combination and is_mandatory:
                # Check if all defined Sub-valor for this VI are present for this patient
                # Convert None from file to "Nulo" string if that's how vi_defined_descriptors stores them,
                # but vi_defined_descriptors should store actual sub-valor names.
                # descriptors_used_by_patient_for_vi contains actual names or None.
                
                actual_descriptors_present = {d for d in descriptors_used_by_patient_for_vi if d is not None}

                missing_descriptors = vi_defined_descriptors - actual_descriptors_present
                if missing_descriptors:
                    error_messages.append(
                        f"Participante '{patient_id}': Para la VI '{vi_name}' (múltiple y obligatoria), "
                        f"faltan los siguientes sub-valores: {', '.join(sorted(list(missing_descriptors)))}. "
                        f"Cada participante debe tener al menos un archivo para cada sub-valor de esta VI."
                    )
    
    if error_messages:
        logger.warning(f"Errores de validación de reglas de VI: {error_messages}")
    return error_messages
