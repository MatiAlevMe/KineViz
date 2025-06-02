# KineViz Architecture Overview                                                                                                  
                                                                                                                                
## 1. Introduction                                                                                                               
Briefly describe the purpose of KineViz and its main goals.                                                                      
                                                                                                                                
## 2. Project Structure                                                                                                          
(You can reference or briefly reiterate the folder structure from ROADMAP.md if it's stable, or provide a more focused view on   
key directories like `core`, `ui`, `database`).                                                                                  
                                                                                                                                
## 3. Core Modules and Responsibilities                                                                                          
                                                                                                                                
### 3.1. `kineviz.core` - Business Logic and Domain                                                                              
*   **`core.services`**:                                                                                                         
    *   `StudyService`: Manages CRUD operations for studies, handles study data, VIs, and aliases.                               
    *   `FileService`: Manages file operations within studies (adding, deleting, listing, processing raw files, retrieving unique
parameters from files).                                                                                                          
    *   `AnalysisService`: Contains logic for all types of analyses (discrete, continuous), report generation, data aggregation, 
and statistical computations.                                                                                                    
*   **`core.data_processing`**:                                                                                                  
    *   `file_handlers`: Responsible for reading and interpreting raw data files, extracting metadata, and initial processing.   
    *   `processors`: Contains utility functions for data transformation, calculations (max, min, range), etc., on DataFrames.   
    *   `directory_manager`: Manages the creation and structure of study and patient directories.                                
*   **`core.exceptions`**: Custom exception classes for the application.                                                         
                                                                                                                                
### 3.2. `kineviz.ui` - User Interface Layer                                                                                     
*   **`ui.main_window.py` (`MainWindow`)**: The main application window, orchestrates views and dialogs, holds service instances.
*   **`ui.views`**:                                                                                                              
    *   `LandingPage`: Initial view when no studies exist.                                                                       
    *   `MainView`: Displays the list of studies.                                                                                
    *   `StudyView`: Detailed view for a single study, including file browser and analysis options.                              
    *   `DiscreteAnalysisView`: View for managing and displaying results of discrete analyses.                                   
    *   *(Future: `ContinuousAnalysisView`)*                                                                                     
*   **`ui.dialogs`**: Modal windows for specific tasks.                                                                          
    *   `StudyDialog`: For creating and editing study metadata (including VIs).                                                  
    *   `FileDialog`: For adding files to a study.                                                                               
    *   `DescriptorAliasDialog`: For managing aliases for VI descriptors.                                                        
    *   `ConfigureIndividualAnalysisDialog`: For setting up parameters for a discrete individual analysis.                       
    *   `IndividualAnalysisManagerDialog`: For listing, viewing, and deleting saved individual analyses.                         
    *   `ContinuousAnalysisConfigDialog`: For configuring continuous analysis parameters.                                        
    *   `ConfigDialog`: For application-level settings.                                                                          
*   **`ui.widgets`**: Reusable UI components (e.g., `FileBrowser`, `charting`).                                                  
*   **`ui.utils`**: UI-specific utilities (e.g., `validators`).                                                                  
                                                                                                                                
### 3.3. `kineviz.database` - Data Persistence                                                                                   
*   **`database.repositories.StudyRepository`**: Implements the Repository pattern for database interactions related to studies  
(SQLite). Handles table creation and CRUD.                                                                                       
                                                                                                                                
### 3.4. `kineviz.config` - Application Configuration                                                                            
*   **`config.settings.AppSettings`**: Manages loading and saving application settings from `config.ini`.                        
                                                                                                                                
## 4. Key Data Flows (Examples)                                                                                                  
                                                                                                                                
*   **Creating a New Study:**                                                                                                    
    1.  `MainWindow` -> `StudyDialog` opens.                                                                                     
    2.  User inputs data in `StudyDialog`.                                                                                       
    3.  On save, `StudyDialog` calls `StudyService.create_study()`.                                                              
    4.  `StudyService` validates data, interacts with `StudyRepository.create_study()`.                                          
    5.  `StudyRepository` writes to the database.                                                                                
    6.  `DirectoryManager.crear_estructura_estudio()` is called to create the folder.                                            
    7.  `MainWindow` refreshes `MainView`.                                                                                       
                                                                                                                                
*   **Adding a File to a Study:**                                                                                                
    1.  `StudyView` -> `FileDialog` opens.                                                                                       
    2.  User selects files.                                                                                                      
    3.  `FileDialog` calls `FileService.add_files_to_study()`.                                                                   
    4.  `FileService` validates filenames against study VIs (using `validators`), copies files, processes them (using            
`file_handlers`), and saves processed versions.                                                                                  
    5.  `StudyView` refreshes `FileBrowser`.                                                                                     
                                                                                                                                
*   **Performing a Discrete Individual Analysis:**                                                                               
    1.  `DiscreteAnalysisView` -> `IndividualAnalysisManagerDialog` -> `ConfigureIndividualAnalysisDialog`.                      
    2.  User configures analysis.                                                                                                
    3.  Dialog calls `AnalysisService.perform_individual_analysis()`.                                                            
    4.  `AnalysisService` reads data from summary tables (CSVs), performs stats (scipy), generates plots (`charting`), and saves 
results (config.json, plot.png).                                                                                                 
                                                                                                                                
## 5. Important Design Patterns / Conventions                                                                                    
*   **Service Layer**: Centralizes business logic.                                                                               
*   **Repository Pattern**: Decouples business logic from data access specifics.                                                 
*   **Model-View-Controller (MVC) like separation**: `ui` (View/Controller aspects), `core.services` (Controller/Model aspects), 
`database` (Model aspects).                                                                                                      
*   **Tkinter for UI**: Standard library GUI.                                                                                    
*   **Logging**: Consistent use of Python's `logging` module.                                                                    
                                                                                                                                
## 6. Key Data Structures / DTOs                                                                                                 
*   **Study Object/Dictionary**: Structure used by `StudyService` (name, VIs, aliases, etc.).                                    
*   **Independent Variable (VI) Structure**: `[{'name': str, 'descriptors': list[str], 'allows_combination': bool,               
'is_mandatory': bool}, ...]`.                                                                                                    
*   **File Information Dictionaries**: Used by `FileService` and `FileBrowser` (path, name, type, frequency, etc.).              
*   **Analysis Configuration Dictionaries**: Passed to and saved by `AnalysisService`.                                           
                                                                                                                                
## 7. Notes on "Nulo"                                                                                                            
*   Explain the concept of "Nulo" as a valid descriptor value and how it's handled in filenames and logic.    