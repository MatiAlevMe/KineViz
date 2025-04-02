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

    # Validar que no haya valores duplicados entre tipos y periodos de prueba si ambos existen
    tipos_prueba_str = data.get('test_types', '')
    periodos_prueba_str = data.get('test_periods', '')

    if tipos_prueba_str and periodos_prueba_str: # Solo validar si ambos campos tienen contenido
        tipos_prueba = {x.strip() for x in tipos_prueba_str.split(',') if x.strip()}
        periodos_prueba = {x.strip() for x in periodos_prueba_str.split(',') if x.strip()}
        duplicates = tipos_prueba.intersection(periodos_prueba)
        if duplicates:
            return False, f"Los siguientes valores están duplicados entre Tipos y Periodos de prueba: {', '.join(duplicates)}"

    # Si todas las validaciones pasan
    return True, None
