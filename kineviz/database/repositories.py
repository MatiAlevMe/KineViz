import sqlite3
import os
import logging
import json # Importar json
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class StudyRepository:
    def __init__(self, db_path='kineviz.db', studies_base_dir=None):
        """
        Inicializa el repositorio.

        :param db_path: Ruta al archivo de la base de datos SQLite.
        :param studies_base_dir: Ruta base para las carpetas de estudios. Si es None,
                                 se calcula relativo a la raíz del proyecto.
        """
        self.db_path = db_path
        if studies_base_dir:
            self.studies_base_dir = Path(studies_base_dir)
        else:
            # Calcular ruta base por defecto relativa a la raíz del proyecto
            self.studies_base_dir = Path(__file__).resolve().parent.parent.parent / 'estudios'
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
                    nombre_estudio TEXT NOT NULL UNIQUE,
                    num_sujetos INTEGER NOT NULL,
                    cantidad_intentos_prueba INTEGER NOT NULL,
                    independent_variables TEXT, -- Almacenará JSON con estructura de VIs y Sub-valores
                    aliases TEXT, -- Almacenará JSON con mapeo descriptor -> alias para este estudio
                    is_pinned INTEGER DEFAULT 0 NOT NULL, -- 0 for not pinned, 1 for pinned
                    comentario TEXT -- Comentario para el estudio, max 150 caracteres
                )
            ''')
            # --- Migración Simple ---
            # Intentar añadir las nuevas columnas si no existen
            try:
                cursor.execute("ALTER TABLE estudios ADD COLUMN comentario TEXT")
                logger.info("Columna 'comentario' añadida a la tabla 'estudios'.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e): pass # Columna ya existe
                else: raise
            try:
                cursor.execute("ALTER TABLE estudios ADD COLUMN independent_variables TEXT")
                logger.info("Columna 'independent_variables' añadida a la tabla 'estudios'.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e): pass
                else: raise
            try:
                cursor.execute("ALTER TABLE estudios ADD COLUMN aliases TEXT")
                logger.info("Columna 'aliases' añadida a la tabla 'estudios'.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e): pass
                else: raise
            try:
                cursor.execute("ALTER TABLE estudios ADD COLUMN is_pinned INTEGER DEFAULT 0 NOT NULL")
                logger.info("Columna 'is_pinned' añadida a la tabla 'estudios'.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e): pass # Columna ya existe
                else: raise

            # Intentar eliminar las columnas antiguas si existen (ignorar errores)
            old_columns = ['frecuencias', 'tipos_prueba', 'periodos_prueba']
            for col in old_columns:
                try:
                    # Usar IF EXISTS para simplificar (requiere SQLite >= 3.3)
                    # Si no, mantener el try/except
                    # cursor.execute(f"ALTER TABLE estudios DROP COLUMN IF EXISTS {col}")
                    cursor.execute(f"ALTER TABLE estudios DROP COLUMN {col}")
                    logger.info(f"Columna antigua '{col}' eliminada de la tabla 'estudios'.")
                except sqlite3.OperationalError as e:
                    if "no such column" in str(e) or "Cannot drop column" in str(e): # Manejar error si no existe
                        pass
                    else:
                        logger.warning(f"No se pudo eliminar la columna antigua '{col}': {e}")

            conn.commit()

    def create_study(self, study_data):
        """
        Crea un nuevo estudio en la base de datos.

        :param study_data: Diccionario con datos del estudio, incluyendo
                           'independent_variables' y 'aliases' como strings JSON.
        :return: ID del estudio creado.
        :raises ValueError: Si el nombre del estudio ya existe.
        :raises sqlite3.Error: Para otros errores de base de datos.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO estudios
                    (nombre_estudio, num_sujetos, cantidad_intentos_prueba, independent_variables, aliases, is_pinned, comentario)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    study_data['name'],
                    int(study_data['num_subjects']),
                    int(study_data['attempts_count']),
                    study_data.get('independent_variables', '[]'), # Guardar JSON string
                    study_data.get('aliases', '{}'), # Guardar JSON string
                    study_data.get('is_pinned', 0), # Default to not pinned
                    study_data.get('comentario', None) # Comentario opcional
                ))
                conn.commit()
                study_id = cursor.lastrowid
            except sqlite3.IntegrityError as e:
                 if "UNIQUE constraint failed: estudios.nombre_estudio" in str(e):
                      raise ValueError(f"Ya existe un estudio con el nombre '{study_data['name']}'.")
                 else:
                      raise # Relanzar otros errores de integridad

            # Crear directorio para el estudio usando self.studies_base_dir
            try:
                study_dir = self.studies_base_dir / study_data['name']
                study_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directorio creado para estudio {study_id}: {study_dir}")
            except OSError as e:
                # Si falla la creación del directorio, ¿deberíamos revertir la creación en DB?
                # Por ahora, solo loggeamos el error. Considerar una transacción más compleja.
                logger.error(f"Error al crear directorio para estudio {study_id} ({study_data['name']}): {e}", exc_info=True)
                # Podríamos eliminar el registro recién creado o lanzar una excepción
                # cursor.execute('DELETE FROM estudios WHERE id_estudio = ?', (study_id,))
                # conn.commit()
                # raise IOError(f"Error creando directorio del estudio: {e}") from e

            return study_id
    
    def get_all_studies(self):
        """
        Obtiene todos los estudios
        
        :return: Lista de estudios
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Order by is_pinned descending, then by name ascending
            # Fetch comentario as well
            cursor.execute('SELECT id_estudio, nombre_estudio, is_pinned, comentario FROM estudios ORDER BY is_pinned DESC, nombre_estudio COLLATE NOCASE ASC')
            return [
                {'id': row[0], 'name': row[1], 'is_pinned': row[2], 'comentario': row[3]}
                for row in cursor.fetchall()
            ]
    
    def get_study_by_id(self, study_id):
        """
        Obtiene los detalles de un estudio específico
        
        :param study_id: ID del estudio
        :return: Diccionario con detalles del estudio
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row # Devolver filas como diccionarios
            cursor = conn.cursor()
            # Seleccionar las columnas nuevas
            cursor.execute('''
                SELECT id_estudio, nombre_estudio, num_sujetos, cantidad_intentos_prueba,
                       independent_variables, aliases, is_pinned, comentario
                FROM estudios WHERE id_estudio = ?
            ''', (study_id,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"Estudio con ID {study_id} no encontrado")

            return {
                # Acceder por nombre de columna
                'id': row['id_estudio'],
                'name': row['nombre_estudio'],
                'num_subjects': row['num_sujetos'],
                'attempts_count': row['cantidad_intentos_prueba'],
                'independent_variables': row['independent_variables'], # Devolver como string JSON
                'aliases': row['aliases'], # Devolver como string JSON
                'is_pinned': row['is_pinned'],
                'comentario': row['comentario'] # Devolver comentario
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
                # Eliminar directorio del estudio usando self.studies_base_dir
                study_dir = self.studies_base_dir / study_name[0]
                if study_dir.exists() and study_dir.is_dir():
                    import shutil
                    logger.info(f"Eliminando directorio del estudio: {study_dir}")
                    shutil.rmtree(study_dir, ignore_errors=True) # ignore_errors podría ocultar problemas
                else:
                    logger.warning(f"Directorio del estudio no encontrado o no es un directorio: {study_dir}")
            else:
                 logger.warning(f"No se encontró estudio con ID {study_id} para eliminar directorio.")

            conn.commit() # Asegurar commit después de la operación
            logger.info(f"Estudio ID {study_id} eliminado de la base de datos.")

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
            logger.error(f"Error al contar estudios en '{self.db_path}': {e}", exc_info=True)
            # Considerar lanzar una excepción personalizada o devolver 0/None
            return 0

    def get_studies_paginated(self, limit: int, offset: int, search_term: str = None):
        """
        Obtiene una lista paginada de estudios, opcionalmente filtrada por nombre.

        :param limit: Número máximo de estudios a devolver.
        :param offset: Número de estudios a omitir (para paginación).
        :param search_term: Término de búsqueda para filtrar por nombre_estudio (case-insensitive).
        :return: Lista de diccionarios de estudios.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Fetch comentario as well
                query = 'SELECT id_estudio, nombre_estudio, is_pinned, comentario FROM estudios'
                params = []
                if search_term:
                    query += ' WHERE nombre_estudio LIKE ?'
                    params.append(f'%{search_term}%')
                
                query += ' ORDER BY is_pinned DESC, nombre_estudio COLLATE NOCASE ASC LIMIT ? OFFSET ?'
                params.extend([limit, offset])

                cursor.execute(query, params)
                return [{'id': row[0], 'name': row[1], 'is_pinned': row[2], 'comentario': row[3]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener estudios paginados: {e}", exc_info=True)
            return []

    def get_total_studies_count(self, search_term: str = None):
        """
        Cuenta el número total de estudios, opcionalmente filtrado por nombre.

        :param search_term: Término de búsqueda para filtrar por nombre_estudio (case-insensitive).
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
            logger.error(f"Error al contar estudios filtrados: {e}", exc_info=True)
            return 0

    def update_study(self, study_id: int, study_data: dict):
        """
        Actualiza los datos de un estudio en la base de datos.

        :param study_id: ID del estudio a actualizar.
        :param study_data: Diccionario con los nuevos datos.
                           El campo 'is_pinned' no se actualiza aquí, usar update_study_pin_status.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # is_pinned no se actualiza a través de este método general.
                # Se maneja con update_study_pin_status.
                cursor.execute('''
                    UPDATE estudios
                    SET nombre_estudio = ?,
                        num_sujetos = ?,
                        cantidad_intentos_prueba = ?,
                        independent_variables = ?,
                        aliases = ?,
                        comentario = ?
                    WHERE id_estudio = ?
                ''', (
                    study_data['name'],
                    int(study_data['num_subjects']),
                    int(study_data['attempts_count']),
                    study_data.get('independent_variables', '[]'),
                    study_data.get('aliases', '{}'),
                    study_data.get('comentario', None), # Actualizar comentario
                    study_id
                ))
                conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"Intento de actualizar estudio ID {study_id} fallido (no encontrado).")
                    raise ValueError(f"No se encontró estudio con ID {study_id} para actualizar.")
                logger.info(f"Estudio ID {study_id} actualizado correctamente.")
        except sqlite3.IntegrityError as e:
             if "UNIQUE constraint failed: estudios.nombre_estudio" in str(e):
                  raise ValueError(f"Ya existe un estudio con el nombre '{study_data['name']}'.")
             else:
                  logger.error(f"Error de integridad al actualizar estudio ID {study_id}: {e}", exc_info=True)
                  raise
        except sqlite3.Error as e:
            logger.error(f"Error general de DB al actualizar estudio ID {study_id}: {e}", exc_info=True)
            raise

    def rename_study_folder(self, old_name: str, new_name: str):
        """
        Renombra la carpeta de un estudio.

        :param old_name: Nombre original de la carpeta del estudio.
        :param new_name: Nuevo nombre para la carpeta del estudio.
        """
        # Usar self.studies_base_dir
        old_path = self.studies_base_dir / old_name
        new_path = self.studies_base_dir / new_name

        if old_path.exists() and old_path.is_dir():
            try:
                os.rename(old_path, new_path)
                logger.info(f"Carpeta de estudio renombrada de '{old_name}' a '{new_name}'")
            except OSError as e:
                logger.error(f"Error al renombrar carpeta de estudio de '{old_name}' a '{new_name}': {e}", exc_info=True)
                # Considerar mostrar un error al usuario o relanzar
        elif not old_path.exists():
             logger.warning(f"Carpeta original '{old_name}' no encontrada para renombrar.")
             # Crear la nueva carpeta si no existe la original? Depende del flujo deseado.
             # new_path.mkdir(parents=True, exist_ok=True)

    def update_study_pin_status(self, study_id: int, is_pinned: bool):
        """
        Actualiza el estado de 'pinned' de un estudio.

        :param study_id: ID del estudio a actualizar.
        :param is_pinned: True si el estudio debe ser pineado, False en caso contrario.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE estudios
                    SET is_pinned = ?
                    WHERE id_estudio = ?
                ''', (1 if is_pinned else 0, study_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"Intento de actualizar pin para estudio ID {study_id} fallido (no encontrado).")
                    raise ValueError(f"No se encontró estudio con ID {study_id} para actualizar pin.")
                logger.info(f"Estado de pin para estudio ID {study_id} actualizado a {is_pinned}.")
        except sqlite3.Error as e:
            logger.error(f"Error de DB al actualizar pin para estudio ID {study_id}: {e}", exc_info=True)
            raise

    def count_pinned_studies(self) -> int:
        """
        Cuenta el número total de estudios pineados.

        :return: Número de estudios pineados.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM estudios WHERE is_pinned = 1')
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            logger.error(f"Error al contar estudios pineados: {e}", exc_info=True)
            return 0

    def update_study_comment(self, study_id: int, comment: str | None):
        """
        Actualiza solo el comentario de un estudio específico.

        :param study_id: ID del estudio a actualizar.
        :param comment: Nuevo comentario (puede ser None).
        :raises ValueError: Si el estudio no se encuentra.
        :raises sqlite3.Error: Para otros errores de base de datos.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE estudios
                    SET comentario = ?
                    WHERE id_estudio = ?
                ''', (comment, study_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"Intento de actualizar comentario para estudio ID {study_id} fallido (no encontrado).")
                    raise ValueError(f"No se encontró estudio con ID {study_id} para actualizar comentario.")
                logger.info(f"Comentario para estudio ID {study_id} actualizado.")
        except sqlite3.Error as e:
            logger.error(f"Error de DB al actualizar comentario para estudio ID {study_id}: {e}", exc_info=True)
            raise
        
