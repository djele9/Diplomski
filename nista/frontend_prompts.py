from pathlib import Path

features_dir = Path('../features_stari')
features_files = sorted(features_dir.glob('*.feature'))

if not features_files:
    raise RuntimeError("Feature directory is empty, no feature files found!")

context = ''

for file in features_files:
    context += f'\n\n===== {file.name} =====\n'
    context += file.read_text(encoding='utf-8')



def get_generated_backend_context() -> str:
    backend_dir = Path("app/backend")

    if not backend_dir.exists():
        return ""

    context = ""

    for file in sorted(backend_dir.rglob("*")):
        if file.is_file():
            try:
                content = file.read_text(encoding="utf-8")
                context += f"\n\n===== EXISTING FILE: {file.as_posix()} =====\n"
                context += content
            except UnicodeDecodeError:
                pass

    return context


def get_generated_frontend_context():
    frontend_dir = Path("app/frontend")

    if not frontend_dir.exists():
        return ""

    context = ""

    for file in sorted(frontend_dir.rglob("*")):
        if file.is_file():
            try:
                content = file.read_text(encoding="utf-8")
                context += f"\n\n===== EXISTING FILE: {file.as_posix()} =====\n"
                context += content
            except UnicodeDecodeError:
                pass

    return context


def generate_frontend_models():
    return f'''
        Generate frontend models based strictly on the Gherkin specifications provided below.  
        For implementation use:
    - Angular 20.3.6, standalone components, do not use modules only standalone way 
    - TypeScript
    - HTML
    - CSS
    - Bootstrap and Bootstrap icons

        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        All files must be in frontend/src/app/models

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and eventually update them
        ================ BEGIN BACKEND FILES ================
        {get_generated_backend_context()}
        ================= END BACKEND FILES =================

        Implement every scenario do not use:
        etc.
    TODO
    IMPLEMENT HERE
    IMPLEMENT THIS
    ADD YOUR CODE
    YOUR CODE HERE
    REST OF CODE
    REST OF FILE
    OMITTED
    OMITTED FOR BREVITY

    And never use mock data, json, arrays, only use data from mongo db
        '''


def generate_frontend_services():
    return f'''
        Generate frontend services based strictly on the Gherkin specifications provided below.  
        For implementation use:
    - Angular 20.3.6, standalone components, do not use modules only standalone way 
    - TypeScript
    - HTML
    - CSS
    - Bootstrap and Bootstrap icons

        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        All files must be in frontend/src/app/services

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and eventually update them
        ================ BEGIN BACKEND FILES ================
        {get_generated_backend_context()}
        ================= END BACKEND FILES =================
        
          Use also other files from app/frontend for synchronization and eventually update them
        ================ BEGIN FRONTEND FILES ================
        {get_generated_frontend_context()}
        ================= END FRONTEND FILES =================

        Implement every scenario do not use:
        etc.
    TODO
    IMPLEMENT HERE
    IMPLEMENT THIS
    ADD YOUR CODE
    YOUR CODE HERE
    REST OF CODE
    REST OF FILE
    OMITTED
    OMITTED FOR BREVITY

    And never use mock data, json, arrays, only use data from mongo db
        '''

def generate_frontend_components():
    return f'''
        Generate frontend components based strictly on the Gherkin specifications provided below.  
        For implementation use:
    - Angular 20.3.6, standalone components, do not use modules only standalone way 
    - TypeScript
    - HTML
    - CSS
    - Bootstrap and Bootstrap icons

        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        All files must be in frontend/src/app/components

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and eventually update them
        ================ BEGIN BACKEND FILES ================
        {get_generated_backend_context()}
        ================= END BACKEND FILES =================

          Use also other files from app/frontend for synchronization and eventually update them
        ================ BEGIN FRONTEND FILES ================
        {get_generated_frontend_context()}
        ================= END FRONTEND FILES =================

        Implement every scenario do not use:
        etc.
    TODO
    IMPLEMENT HERE
    IMPLEMENT THIS
    ADD YOUR CODE
    YOUR CODE HERE
    REST OF CODE
    REST OF FILE
    OMITTED
    OMITTED FOR BREVITY

    And never use mock data, json, arrays, only use data from mongo db
        '''

def generate_frontend_guards():
    return f'''
        Generate frontend guards based strictly on the Gherkin specifications provided below.  
        For implementation use:
    - Angular 20.3.6, standalone components, do not use modules only standalone way 
    - TypeScript
    - HTML
    - CSS
    - Bootstrap and Bootstrap icons

        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        All files must be in frontend/src/app/guards

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and eventually update them
        ================ BEGIN BACKEND FILES ================
        {get_generated_backend_context()}
        ================= END BACKEND FILES =================

          Use also other files from app/frontend for synchronization and eventually update them
        ================ BEGIN FRONTEND FILES ================
        {get_generated_frontend_context()}
        ================= END FRONTEND FILES =================

        Implement every scenario do not use:
        etc.
    TODO
    IMPLEMENT HERE
    IMPLEMENT THIS
    ADD YOUR CODE
    YOUR CODE HERE
    REST OF CODE
    REST OF FILE
    OMITTED
    OMITTED FOR BREVITY

    And never use mock data, json, arrays, only use data from mongo db
        '''

def generate_angular_base():
    return f'''
        Generate frontend base files for angular based strictly on the Gherkin specifications provided below.  
        For implementation use:
    - Angular 20.3.6, standalone components, do not use modules only standalone way 
    - TypeScript
    - HTML
    - CSS
    - Bootstrap and Bootstrap icons
    
    Implement this files:
    frontend/src/app/app.config.ts
    frontend/src/app/app.css
    frontend/src/app/app.html
    frontend/src/app/app.routes.ts
    frontend/src/app/app.spec.ts
    frontend/src/app/app.ts
    frontend/src/favicon.ico
    frontend/src/index.html
    frontend/src/main.ts
    frontend/src/styles.css
    make assets folder for images
    frontend/angular.json
    frontend/package-lock.json
    frontend/package.json
    frontend/tsconfig.app.json
    frontend/tsconfig.json
    frontend/tsconfig.spec.json


        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        All files must be in frontend/src/app/services

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and eventually update them
        ================ BEGIN BACKEND FILES ================
        {get_generated_backend_context()}
        ================= END BACKEND FILES =================

          Use also other files from app/frontend for synchronization and eventually update them
        ================ BEGIN FRONTEND FILES ================
        {get_generated_frontend_context()}
        ================= END FRONTEND FILES =================

        Implement every scenario do not use:
        etc.
    TODO
    IMPLEMENT HERE
    IMPLEMENT THIS
    ADD YOUR CODE
    YOUR CODE HERE
    REST OF CODE
    REST OF FILE
    OMITTED
    OMITTED FOR BREVITY

    And never use mock data, json, arrays, only use data from mongo db
        '''