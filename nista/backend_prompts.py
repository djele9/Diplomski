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


def generate_backend_models():
    return f'''
Generate backend Mongoose schemas based strictly on the Gherkin specifications provided below.  
For implementation use:
- Node.js 22.21.0
- Express.js
- TypeScript

Every file format must be:

FILE: relative/path/to/file.ext

```language
COMPLETE FILE CONTENT
```

All files must be in backend/src/models

The following content contains ALL .feature files for the application.
Treat each filename section as a separate Gherkin file.
All of them belong to the same application.

================ BEGIN GHERKIN SPECIFICATIONS ================
{context}
================= END GHERKIN SPECIFICATIONS =================
'''

def generate_backend_controllers():
    return f'''
    Generate backend controllers based strictly on the Gherkin specifications provided below.  
    For implementation use:
    - Node.js 22.21.0
    - Express.js
    - TypeScript

    Every file format must be:

    FILE: relative/path/to/file.ext

    ```language
    COMPLETE FILE CONTENT
    ```

    All files must be in backend/src/controllers

    The following content contains ALL .feature files for the application.
    Treat each filename section as a separate Gherkin file.
    All of them belong to the same application.

    ================ BEGIN GHERKIN SPECIFICATIONS ================
    {context}
    ================= END GHERKIN SPECIFICATIONS =================
    
    Use also other files from app/backend for synchronization and modify them if necessary
    ================ BEGIN BACKEND FILES ================
    {get_generated_backend_context()}
    ================= END BACKEND FILES =================
    
    Implement every scenario and do not use:
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

def generate_backend_routers():
    return f'''
        Generate backend routers based strictly on the Gherkin specifications provided below.  
        For implementation use:
        Backend:
        - Node.js 22.21.0
        - Express.js
        - TypeScript

        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        All files must be in backend/src/routers

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and modify them if necessary
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

def generate_backend_middlewares():
    return f'''
        Generate backend middlewares based strictly on the Gherkin specifications provided below.  
        
        If
        authentication is required, use
        secure
        password
        hashing,
        JWT
        authentication and appropriate
        authorization.
    
        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        All files must be in backend/src/middlewares

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and modify them if necessary
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

def generate_backend_base():
    return f'''
        Generate backend files based strictly on the Gherkin specifications provided below.  
        For implementation use:
        Backend:
        - Node.js 22.21.0
        - Express.js
        - TypeScript
        
        Generate this files:
        backend/src/server.ts
        backend/package-lock.json
        backend/package.json
        backend/tsconfig.json
        backend/env
        
        INITIAL ADMINISTRATOR REQUIREMENTS(IF ADMINISTRATOR IS REQUIRED IN FEATURE FILES):

The application must have an initial administrator account so that the administrator functionality can be used immediately after the application is started.
Do NOT create a public administrator registration page.

The initial administrator account must be created automatically during
backend startup if an administrator account does not already exist.

The administrator credentials must NOT be hardcoded directly in the source code.

Use environment variables for the initial administrator credentials.

Add the following variables to backend/.env:

ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin123!

During backend startup:

1. Connect to MongoDB.
2. Check whether an administrator account already exists.
3. If no administrator account exists, create the initial administrator using ADMIN_USERNAME and ADMIN_PASSWORD from the environment.
4. Hash the administrator password securely before storing it.
5. If an administrator already exists, do not create another one.
6. Do not overwrite or modify an existing administrator password.
        
        Every file format must be:

        FILE: relative/path/to/file.ext

        ```language
        COMPLETE FILE CONTENT
        ```

        The following content contains ALL .feature files for the application.
        Treat each filename section as a separate Gherkin file.
        All of them belong to the same application.

        ================ BEGIN GHERKIN SPECIFICATIONS ================
        {context}
        ================= END GHERKIN SPECIFICATIONS =================

        Use also other files from app/backend for synchronization and modify them if necessary
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

