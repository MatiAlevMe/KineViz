import sqlite3
import os
from pathlib import Path # Importar Path

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
                # Eliminar directorio del estudio si existe
                # Asegurarse de que la ruta base sea correcta (asumiendo que 'estudios' está en la raíz del proyecto)
                # La ruta de la DB puede ser relativa o absoluta, necesitamos la raíz del proyecto
                from pathlib import Path
                project_root_dir = Path(__file__).resolve().parent.parent.parent # Ajustar si la estructura es diferente
                study_dir = project_root_dir / 'estudios' / study_name[0]
                if study_dir.exists() and study_dir.is_dir():
                    import shutil
                    print(f"Eliminando directorio: {study_dir}") # Log
                    shutil.rmtree(study_dir, ignore_errors=True)
                else:
                    print(f"Directorio no encontrado o no es un directorio: {study_dir}") # Log
            else:
                 print(f"No se encontró estudio con ID {study_id} para eliminar directorio.") # Log

            conn.commit() # Asegurar commit después de la operación

    def count_studies(self):
        """
        Cuenta el número total de estudios en la base de datos.

        :return: Número de estudios.
        """
        try:
            # Asegurarse de que la tabla exista antes de contar
            self._create_tables()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM estudios')
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            print(f"Error al contar estudios en '{self.db_path}': {e}")
            # Considerar lanzar una excepción personalizada o devolver 0/None
            return 0

    def get_studies_paginated(self, limit: int, offset: int, search_term: str = None):
        """
        Obtiene una lista paginada de estudios, opcionalmente filtrada por nombre.

        :param limit: Número máximo de estudios a devolver.
        :param offset: Número de estudios a omitir (para paginación).
        :param search_term: Término de búsqueda para filtrar por nombre (case-insensitive).
        :return: Lista de diccionarios de estudios.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = 'SELECT id_estudio, nombre_estudio FROM estudios'
                params = []
                if search_term:
                    query += ' WHERE nombre_estudio LIKE ?'
                    params.append(f'%{search_term}%')
                query += ' ORDER BY nombre_estudio COLLATE NOCASE ASC LIMIT ? OFFSET ?'
                params.extend([limit, offset])

                cursor.execute(query, params)
                return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener estudios paginados: {e}")
            return []

    def get_total_studies_count(self, search_term: str = None):
        """
        Cuenta el número total de estudios, opcionalmente filtrado por nombre.

        :param search_term: Término de búsqueda para filtrar por nombre (case-insensitive).
        :return: Número total de estudios que coinciden.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM estudios'
                params = []
                if search_term:
                    query += ' WHERE nombre_estudio LIKE ?'
                    params.append(f'%{search_term}%')

                cursor.execute(query, params)
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            print(f"Error al contar estudios filtrados: {e}")
            return 0

    def update_study(self, study_id: int, study_data: dict):
        """
        Actualiza los datos de un estudio en la base de datos.

        :param study_id: ID del estudio a actualizar.
        :param study_data: Diccionario con los nuevos datos.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE estudios
                    SET nombre_estudio = ?,
                        num_sujetos = ?,
                        tipos_prueba = ?,
                        periodos_prueba = ?,
                        cantidad_intentos_prueba = ?
                    WHERE id_estudio = ?
                ''', (
                    study_data['name'],
                    int(study_data['num_subjects']),
                    study_data['test_types'],
                    study_data['test_periods'],
                    int(study_data['attempts_count']),
                    study_id
                ))
                conn.commit()
                if cursor.rowcount == 0:
                    raise ValueError(f"No se encontró estudio con ID {study_id} para actualizar.")
        except sqlite3.Error as e:
            print(f"Error al actualizar estudio ID {study_id}: {e}")
            # Considerar relanzar una excepción personalizada
            raise

    def rename_study_folder(self, old_name: str, new_name: str):
        """
        Renombra la carpeta de un estudio.

        :param old_name: Nombre original de la carpeta del estudio.
        :param new_name: Nuevo nombre para la carpeta del estudio.
        """
        project_root_dir = Path(__file__).resolve().parent.parent.parent
        old_path = project_root_dir / 'estudios' / old_name
        new_path = project_root_dir / 'estudios' / new_name

        if old_path.exists() and old_path.is_dir():
            try:
                os.rename(old_path, new_path)
                print(f"Carpeta renombrada de '{old_name}' a '{new_name}'")
            except OSError as e:
                print(f"Error al renombrar carpeta de '{old_name}' a '{new_name}': {e}")
                # Considerar mostrar un error al usuario o loggear
        elif not old_path.exists():
             print(f"Advertencia: Carpeta original '{old_name}' no encontrada para renombrar.")
             # Crear la nueva carpeta si no existe la original? Depende del flujo deseado.
             # new_path.mkdir(parents=True, exist_ok=True)
