class FileHandlerError(Exception):                                                                                                                             
    """Base exception for file handling errors"""                                                                                                              
    def __init__(self, message="File processing error"):                                                                                                       
        self.message = message                                                                                                                                 
        super().__init__(self.message)                                                                                                                         
                                                                                                                                                               
class FileNotFoundError(FileHandlerError):                                                                                                                     
    """Raised when a file is not found"""                                                                                                                      
    def __init__(self, path):                                                                                                                                  
        self.path = path                                                                                                                                       
        super().__init__(f"Archivo no encontrado: {path}")                                                                                                     
                                                                                                                                                               
class InvalidFileFormatError(FileHandlerError):                                                                                                                
    """Invalid file format or content"""                                                                                                                       
    def __init__(self, detail=""):                                                                                                                             
        msg = "Formato de archivo inválido"                                                                                                                    
        if detail: msg += f": {detail}"                                                                                                                        
        super().__init__(msg)                                                                                                                                  
                                                                                                                                                               
class IOError(FileHandlerError):                                                                                                                               
    """General I/O exception"""                                                                                                                                
    def __init__(self, detail=""):                                                                                                                             
        msg = "Error de entrada/salida"                                                                                                                        
        if detail: msg += f": {detail}"                                                                                                                        
        super().__init__(msg)  