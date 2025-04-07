# KineViz Refactoring Roadmap

Este roadmap describe el proceso de refactorización de la aplicación KineViz, moviendo la lógica original de los archivos `interfaz.py` y `lectura.py` a una estructura modular basada en servicios, repositorios y componentes de UI reutilizables dentro del paquete `kineviz`. El objetivo es mejorar la mantenibilidad, escalabilidad y organización del código.

Este ROADMAP debe ser actualizado en cada iteración hasta completar la refactorización y se debe dar la opción de ejecutar el programa con "python -m kineviz.app" para ir capturando errores.

## Fase 1: Integración Inicial y Estructura Base (Completada - d2caeef)

*   [x] Crear estructura básica del proyecto (`kineviz` package).
*   [x] Mover lógica de `lectura.py` a `kineviz.core.data_processing` y `kineviz.core.services`.
*   [x] Crear punto de entrada `kineviz/app.py`.
*   [x] Refactorizar `kineviz/ui/main_window.py` para manejar la ventana principal, configuración inicial y navegación básica.
*   [x] Integrar `LandingPage` (`kineviz/ui/views/landing_page.py`).
*   [x] Integrar diálogo de creación/edición de estudios (`kineviz/ui/dialogs/study_dialog.py`) con validación básica.
*   [x] Adaptar `StudyService` y `StudyRepository` para soportar operaciones básicas y conteo.
*   [x] Corregir errores iniciales de importación y validación.

## Fase 2: Vista Principal y Gestión de Estudios

*   [x] Implementar `MainView` (`kineviz/ui/views/main_view.py`) para mostrar la lista de estudios.
    *   [x] Tabla de estudios (`ttk.Treeview`).
    *   [x] Funcionalidad de búsqueda.
    *   [x] Paginación de estudios.
    *   [x] Botones de acción (Ver, Editar, Eliminar) en la tabla.
    *   [x] Botones de cabecera (Manual, Config, Ayuda, Abrir Carpeta).
*   [x] Implementar la funcionalidad completa de **Editar Estudio** en `StudyDialog` y `StudyService`/`StudyRepository`.
    *   [x] Cargar datos existentes en el diálogo.
    *   [x] Validar datos modificados.
    *   [x] Actualizar datos en la base de datos (`StudyService.update_study`).
    *   [x] Renombrar carpeta del estudio si el nombre cambia (`StudyRepository.rename_study_folder`).
    *   [x] Manejar la validación/eliminación de archivos existentes si los criterios (tipos/periodos) cambian.
*   [x] Implementar la funcionalidad de **Eliminar Estudio** en `MainView` y `StudyService`/`StudyRepository`.
*   [x] Implementar la funcionalidad de **Ver Estudio** (`StudyView`).
    *   [x] Mostrar detalles básicos del estudio.
    *   [x] Integrar `FileBrowser` para mostrar archivos del estudio.
    *   [x] Implementar carga real de archivos en `FileBrowser` desde `FileService`.
    *   [x] Funcionalidad "Ver Archivo".
    *   [x] Funcionalidad "Eliminar Archivo".

## Fase 3: Gestión de Archivos y Análisis

*   [x] Implementar `FileBrowser` (`kineviz/ui/widgets/file_browser.py`) completamente.
    *   [x] Cargar y mostrar archivos del estudio desde `FileService`. (Hecho en Fase 2)
    *   [x] Paginación de archivos.
    *   [x] Búsqueda/filtrado de archivos.
    *   [x] Funcionalidad "Ver Archivo". (Hecho en Fase 2)
    *   [x] Funcionalidad "Eliminar Archivo". (Hecho en Fase 2)
*   [x] Implementar `FileService` para manejar la lógica de archivos (obtener, eliminar, filtrar, paginar, agregar). (Hecho en Fase 2 y 3)
*   [x] Implementar diálogo para **Agregar Archivos** a un estudio, incluyendo validación de formato de nombre.
*   [ ] Implementar `AnalysisDialog` (`kineviz/ui/dialogs/analysis_dialog.py`).
    *   [x] Selección de parámetros (pacientes, frecuencias, tipos, periodos, cálculos).
    *   [ ] Generación de reportes PDF.
    *   [ ] Visualización/eliminación de reportes generados.
*   [x] Implementar `AnalysisService` para la lógica de análisis y generación de reportes. (Implementación inicial de PDF y cálculos)
*   [x] Implementar `Charting` (`kineviz/ui/widgets/charting.py`) para visualizaciones. (Boxplot, Barchart básicos)
*   [ ] Implementar visualización/eliminación de reportes generados en `AnalysisDialog`.

## Fase 4: Refinamientos y Finalización

*   [ ] Implementar `ConfigDialog` (`kineviz/ui/dialogs/config_dialog.py`) y `AppSettings` (`kineviz/config/settings.py`).
*   [ ] Mejorar manejo de errores y logging (`kineviz/utils/logger.py`).
*   [ ] Añadir pruebas unitarias e de integración (`tests/`).
*   [ ] Completar documentación (`docs/`).
*   [ ] Limpiar código remanente de `interfaz.py` y `lectura.py`.
*   [ ] Revisión final de estilos y UX.

---

## Known Issues / Bugs

*   **Edición de Estudio - Cambio de Criterios**: Al editar un estudio y cambiar los `Tipos de Prueba` o `Periodos de Prueba`, no se validan ni eliminan automáticamente los archivos existentes que ya no cumplen con los nuevos criterios. (Ver Fase 2 - Editar Estudio).
*   **Análisis y Reportes**: La lógica de análisis y generación de PDF está implementada en `AnalysisService`. Falta integrar la visualización/eliminación de reportes en `AnalysisDialog`. (Ver Fase 3).
*   **Configuración**: El diálogo de configuración (`ConfigDialog`) y el manejo centralizado de ajustes (`AppSettings`) están pendientes. (Ver Fase 4).
*   **Limpieza de Directorios**: La limpieza de directorios vacíos (paciente, frecuencia) después de eliminar el último archivo dentro de ellos funciona, pero podría mejorarse para manejar casos borde o errores de permisos de forma más robusta.
*   **Validación de Pacientes para Análisis**: La validación ahora se basa en los parámetros únicos extraídos de archivos procesados válidos. Si un estudio tiene archivos pero no cumplen los criterios o solo tiene archivos OG, no permitirá el análisis.
*   **Lectura de Datos Procesados**: La función `_read_processed_file_data` en `AnalysisService` asume un formato específico (';' como separador, 4 líneas de header, 3 de stats). Podría ser más robusta o configurable.

---
*Este archivo se actualizará a medida que avance el desarrollo.*
