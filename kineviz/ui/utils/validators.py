def validate_study_data(data):
    """
    Valida los datos de un estudio
    
    :param data: Diccionario con datos del estudio
    :return: Booleano indicando si los datos son válidos
    """
    # Validar nombre
    if not data.get('name') or len(data['name'].strip()) < 3:
        return False
    
    # Validar número de sujetos
    try:
        num_subjects = int(data.get('num_subjects', 0))
        if num_subjects <= 0:
            return False
    except ValueError:
        return False
    
    # Validar tipos de prueba
    if not data.get('test_types'):
        return False
    
    # Validar periodos de prueba
    if not data.get('test_periods'):
        return False
    
    # Validar cantidad de intentos
    try:
        attempts = int(data.get('attempts_count', 0))
        if attempts <= 0:
            return False
    except ValueError:
        return False
    
    return True
