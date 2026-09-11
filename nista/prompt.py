def prompt1(context) -> str:
    return f"""
You are a senior full-stack software engineer.

Generate a complete, runnable full-stack web application based strictly
on the Gherkin specifications provided below.

The Gherkin specifications are the source of truth.

You must analyze ALL provided feature files and implement ALL of their
requirements in ONE coherent application.

Do not assume in advance what functionality the application contains.
The functionality must be determined entirely from the provided
Gherkin specifications.

Technology stack:

Frontend:
- Angular 20.3.6, standalone components, do not use modules only standalone way 
- TypeScript
- HTML
- CSS
- Bootstrap and Bootstrap icons

Backend:
- Node.js 22.21.0
- Express.js

Database:
- MongoDB
- Mongoose

General requirements:

1. Implement every Feature and every Scenario from every provided Gherkin file.

2. Implement every Given, When, Then and And step.

3. Implement both positive and negative scenarios.

4. Use MongoDB for persistent application data.

5. Use Mongoose for database models.

6. Do not use mock data, arrays, JSON files or in-memory storage instead of MongoDB.

7. Generate a complete Angular frontend.

7.1. The Angular frontend MUST include all standard Angular project
bootstrap and configuration files required to build and run the
application.

At minimum, the frontend MUST contain:

- frontend/package.json
- frontend/angular.json
- frontend/tsconfig.json
- frontend/tsconfig.app.json
- frontend/src/index.html
- frontend/src/main.ts
- frontend/src/styles.css

Do not omit any of these files.

8. Generate a complete Node.js/Express backend.

9. Generate all required database models.

10. Generate all required API endpoints.

11. Generate all required Angular components.

12. Generate all required Angular services.

13. Generate all required Angular routes.

14. Generate authentication and authorization only when required
    by the Gherkin specification.

15. If authentication is required, use secure password hashing,
    JWT authentication and appropriate authorization.

16. Implement all validation and error handling required by the specification.

17. Do not invent unrelated functionality.

18. Do not omit functionality described by the Gherkin files.

19. All provided feature files describe ONE application. Combine their requirements into one coherent project.

20. Do not generate one separate application for each feature file.

21. If test data is required, explain in the README how it can be inserted during development without exposing unnecessary 
public production functionality.

UI/UX AND VISUAL DESIGN REQUIREMENTS:

The application must have a modern, polished and professional visual design.
Do NOT create a plain application with a predominantly white, unstyled background.
Do NOT use the default browser appearance.
Do NOT create pages that look like raw HTML forms.
Use Bootstrap and Bootstrap Icons consistently, together with custom CSS where necessary.


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

The README must clearly explain how the initial administrator account
is created and how its credentials can be configured through the
.env file.

The administrator must be able to log in through a dedicated
administrator login page.

Administrator authentication must use the same secure authentication
mechanism required by the application, including password hashing,
JWT authentication and authorization.

Administrator-only API endpoints must be protected by authorization
middleware.

Design requirements:
- Use a modern color palette with a primary color, secondary colors,
  neutral backgrounds and appropriate accent colors.
- Use a visually appealing page background instead of a completely
  plain white background.
- Use cards, panels, sections, spacing, borders, shadows and rounded
  corners where appropriate.
- Forms must look like modern web application forms.
- Buttons must have clear visual hierarchy and hover states.
- Navigation bars must be professionally styled.
- Tables, alerts, forms and dashboards must have consistent styling.
- Use Bootstrap Icons where appropriate.
- Use responsive design so the application works on desktop, tablet
  and mobile screens.
- Maintain consistent typography, spacing and component styling
  throughout the entire application.
- Use visual feedback for loading, success, warning and error states.
- Avoid excessive use of bright colors.
- Avoid excessive gradients, animations or decorative elements.
- Keep the interface professional and suitable for a real member
  management system.


The application should look like a finished professional web
application, not a generated prototype or a collection of default
Bootstrap forms.

Before generating the files, determine a coherent visual design system
and use it consistently across all pages.


Never write:
...
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

Every generated file must contain its complete contents.
Do not provide pseudocode.
Do not provide partial implementations.


OUTPUT FORMAT

Your response must contain exactly two major parts.
PART 1 - PROJECT STRUCTURE
First output the complete directory tree of the generated project.
The tree must contain every file that you generate.
Do not use placeholders in the tree.

PART 2 - COMPLETE FILE CONTENTS
After the project tree, output:
PART 2 - COMPLETE FILE CONTENTS
Then output every generated file using this exact format:


For every file, output exactly:

FILE: relative/path/to/file.ext

```language
COMPLETE FILE CONTENT
```

GHERKIN SPECIFICATIONS

The following content contains ALL .feature files for the application.
Treat each filename section as a separate Gherkin file.
All of them belong to the same application.

================ BEGIN GHERKIN SPECIFICATIONS ================
{context}
================= END GHERKIN SPECIFICATIONS =================

FINAL INSTRUCTION
Now generate the complete application.
First output the complete project structure.
Then output the complete contents of every generated file.
Do not explain what I should implement myself.
Do not provide examples.
Do not provide pseudocode.
Do not provide partial code.
Do not omit files.
Generate the complete runnable application.
"""