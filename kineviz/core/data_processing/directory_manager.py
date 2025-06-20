from pathlib import Path                                                                                                                                       
import shutil                                                                                                                                   
                                                                                                                                                               
def crear_estructura_estudio(nombre_estudio):                                                                                                                  
    base_path = Path("estudios") / nombre_estudio                                                                        
    carpetas = ["OG", "Cinematica", "Cinetica", "Electromiografica", "Desconocida"]                                                           
    for carpeta in carpetas:
        (base_path / carpeta).mkdir(parents=True, exist_ok=True)                                                                                                                                                                                                                                                       
    return base_path                                                                                   
                                                                                                                                                               
def crear_estructura_paciente(ruta_estudio, nombre_paciente):                                                                                                  
    paciente_path = ruta_estudio / nombre_paciente                                                                                                             
    frecuencia = ["OG", "Cinematica", "Cinetica", "Electromiografica"]                                                                                                                                                                                                                       
    for folder in frecuencia:                                                                                                                              
        (paciente_path / folder).mkdir(parents=True, exist_ok=True)
    return paciente_path

# Ya no se usa, la lógica se movió a file_handlers._determinar_frecuencia_por_contenido
# def determinar_tipo_frecuencia(num_frames: int) -> str:
#     if 100 <= num_frames <= 200:
#         return "Cinematica"
#     elif num_frames == 1000:
#         return "Cinetica"
#     elif num_frames == 2000:
#         return "Electromiografica"
#     return "Desconocida"

def crear_carpeta_frecuencia(base_path: Path, tipo: str) -> Path:
    """Crea una carpeta para un tipo de frecuencia específico si no existe."""
    path = base_path / tipo
    path.mkdir(exist_ok=True)
    return path                                                                                 
                                                                                                                                                               
def copiar_archivo_origen(ruta_origen, ruta_destino):                                                                                                          
    shutil.copy2(ruta_origen, ruta_destino)  
