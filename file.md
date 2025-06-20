mermaid
graph TD
    subgraph "Usuario"
        direction LR
        U[Usuario Interfaz]
    end

    subgraph "KineViz Aplicación"
        direction TB

        UI["<b>Capa de Interfaz de Usuario (kineviz.ui)</b><br/>- MainWindow<br/>- Vistas (Landing, Main, Study, Analysis)<br/>- Diálogos (Study, File, Config, Analysis, Backup)<br/>- Widgets (FileBrowser, Charting)"]
        CORE["<b>Capa de Lógica de Negocio (kineviz.core)</b><br/>- Services (StudyService, FileService, AnalysisService)<br/>- Data Processing (file_handlers, processors, directory_manager)<br/>- BackupManager<br/>- UndoManager<br/>- Exceptions"]
        DATABASE["<b>Capa de Persistencia de Datos (kineviz.database)</b><br/>- StudyRepository (SQLite)"]
        CONFIG["<b>Capa de Configuración (kineviz.config)</b><br/>- AppSettings (config.ini)"]
        UTILS["<b>Capa de Utilidades (kineviz.utils)</b><br/>- Logger<br/>- Paths"]
        FILESYS["<b>Sistema de Archivos Local</b><br/>- Directorios de Estudios<br/>- Archivos de Datos (OG, Procesados)<br/>- Resultados de Análisis<br/>- Backups"]

        U -- Interactúa con --> UI

        UI -- Usa / Llama a --> CORE
        CORE -- Usa / Llama a --> DATABASE
        CORE -- Usa / Llama a --> CONFIG
        CORE -- Usa / Llama a --> UTILS
        CORE -- Gestiona / Accede a --> FILESYS

        DATABASE -- Accede a --> FILESYS_DB[(kineviz.db)]
        CONFIG -- Accede a --> FILESYS_CFG[(config.ini)]
    end

    style UI fill:#f9f,stroke:#333,stroke-width:2px
    style CORE fill:#ccf,stroke:#333,stroke-width:2px
    style DATABASE fill:#cfc,stroke:#333,stroke-width:2px
    style CONFIG fill:#ffc,stroke:#333,stroke-width:2px
    style UTILS fill:#eee,stroke:#333,stroke-width:2px
    style FILESYS fill:#cff,stroke:#333,stroke-width:2px
