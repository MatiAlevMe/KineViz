# KineViz Refactoring Roadmap

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
*   [ ] Implementar la funcionalidad completa de **Editar Estudio** en `StudyDialog` y `StudyService`/`StudyRepository`. (Parcialmente hecho, falta manejo de archivos)
*   [x] Implementar la funcionalidad de **Eliminar Estudio** en `MainView` y `StudyService`/`StudyRepository`.
*   [ ] Implementar la funcionalidad de **Ver Estudio** (`StudyView`).
    *   [ ] Mostrar detalles básicos del estudio.
    *   [ ] Integrar `FileBrowser` para mostrar archivos del estudio.

## Fase 3: Gestión de Archivos y Análisis

*   [ ] Implementar `FileBrowser` (`kineviz/ui/widgets/file_browser.py`) completamente.
    *   [ ] Cargar y mostrar archivos del estudio desde `FileService`.
    *   [ ] Paginación de archivos.
    *   [ ] Búsqueda/filtrado de archivos.
    *   [ ] Funcionalidad "Ver Archivo".
    *   [ ] Funcionalidad "Eliminar Archivo".
*   [ ] Implementar `FileService` para manejar la lógica de archivos (obtener, eliminar).
*   [ ] Implementar diálogo para **Agregar Archivos** a un estudio, incluyendo validación de formato de nombre.
*   [ ] Implementar `AnalysisDialog` (`kineviz/ui/dialogs/analysis_dialog.py`).
    *   [ ] Selección de parámetros (pacientes, frecuencias, tipos, periodos, cálculos).
    *   [ ] Generación de reportes PDF.
    *   [ ] Visualización/eliminación de reportes generados.
*   [ ] Implementar `AnalysisService` para la lógica de análisis y generación de reportes.
*   [ ] Implementar `Charting` (`kineviz/ui/widgets/charting.py`) para visualizaciones.

## Fase 4: Refinamientos y Finalización

*   [ ] Implementar `ConfigDialog` (`kineviz/ui/dialogs/config_dialog.py`) y `AppSettings` (`kineviz/config/settings.py`).
*   [ ] Mejorar manejo de errores y logging (`kineviz/utils/logger.py`).
*   [ ] Añadir pruebas unitarias e de integración (`tests/`).
*   [ ] Completar documentación (`docs/`).
*   [ ] Limpiar código remanente de `interfaz.py` y `lectura.py`.
*   [ ] Revisión final de estilos y UX.

---
*Este archivo se actualizará a medida que avance el desarrollo.*
