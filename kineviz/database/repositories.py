import sqlite3
import os

class StudyRepository:
    def __init__(self, db_path='kineviz.db'):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """
        Crea las tablas necesarias si no existen
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estudios (
                    id_estudio INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_estudio TEXT NOT NULL,
                    num_sujetos INTEGER NOT NULL,
                    tipos_prueba TEXT,
                    periodos_prueba TEXT,
                    cantidad_intentos_prueba INTEGER NOT NULL
                )
            ''')
            conn.commit()
    
    def create_study(self, study_data):
        """
        Crea un nuevo estudio en la base de datos
        
        :param study_data: Diccionario con datos del estudio
        :return: ID del estudio creado
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO estudios 
                (nombre_estudio, num_sujetos, tipos_prueba, periodos_prueba, cantidad_intentos_prueba)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                study_data['name'], 
                int(study_data['num_subjects']), 
                study_data['test_types'], 
                study_data['test_periods'], 
                int(study_data['attempts_count'])
            ))
            conn.commit()
            
            # Crear directorio para el estudio
            study_dir = os.path.join('estudios', study_data['name'])
            os.makedirs(study_dir, exist_ok=True)
            
            return cursor.lastrowid
    
    def get_all_studies(self):
        """
        Obtiene todos los estudios
        
        :return: Lista de estudios
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id_estudio, nombre_estudio FROM estudios')
            return [
                {'id': row[0], 'name': row[1]} 
                for row in cursor.fetchall()
            ]
    
    def get_study_by_id(self, study_id):
        """
        Obtiene los detalles de un estudio específico
        
        :param study_id: ID del estudio
        :return: Diccionario con detalles del estudio
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM estudios WHERE id_estudio = ?', (study_id,))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Estudio con ID {study_id} no encontrado")
            
            return {
                'id': row[0],
                'name': row[1],
                'num_subjects': row[2],
                'test_types': row[3],
                'test_periods': row[4],
                'attempts_count': row[5]
            }
    
    def delete_study(self, study_id):
        """
        Elimina un estudio de la base de datos
        
        :param study_id: ID del estudio a eliminar
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Obtener nombre del estudio antes de eliminarlo
            cursor.execute('SELECT nombre_estudio FROM estudios WHERE id_estudio = ?', (study_id,))
            study_name = cursor.fetchone()
            
            if study_name:
                # Eliminar registro de la base de datos
                cursor.execute('DELETE FROM estudios WHERE id_estudio = ?', (study_id,))
                
                # Eliminar directorio del estudio
                study_dir = os.path.join('estudios', study_name[0])
                import shutil
                shutil.rmtree(study_dir, ignore_errors=True)
