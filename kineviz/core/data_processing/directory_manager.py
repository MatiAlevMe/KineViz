from pathlib import Path                                                                                                                                       
import shutil                                                                                                                                   
                                                                                                                                                               
def crear_estructura_estudio(nombre_estudio):                                                                                                                  
    base_path = Path("estudios") / nombre_estudio                                                                                                              
    estructura = {                                                                                                                                             
        "OG": {},                                                                                                                                              
        "Cinematica": {},                                                                                                                                      
        "Cinetica": {},                                                                                                                                        
        "Electromiografica": {},                                                                                                                               
        "Desconocida": {}                                                                                                                                      
    }                                                                                                                                                          
                                                                                                                                                               
    for folder, subfolders in estructura.items():                                                                                                              
        (base_path / folder).mkdir(parents=True, exist_ok=True)                                                                                                
                                                                                                                                                               
def copiar_archivo_origen(ruta_origen, ruta_destino):                                                                                                          
    shutil.copy2(ruta_origen, ruta_destino)  