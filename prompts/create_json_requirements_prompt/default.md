# Create JSON Requirements Prompt

Based on the following project description, create a detailed requirements definition:

Produce only the JSON without any comments or additional text.

It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.

{project_description}

Make sure to use the full filename with its extension for the "name" field within "files".

Ensure that ALL fields are properly filled and that there are NO empty arrays or objects.
Include at least one item in each array (features, tech_stack, files, etc.).
For the folder structure, provide a realistic and comprehensive structure that reflects the project's complexity.
Include a main file (e.g., main.py, index.js) in the appropriate location.

It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
You need to think through every detail and edge case for each component:
Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

Provide the requirements in the following JSON format:
```json
{
    "project_name": "string",
    "description": "string",
    "features": [
        {
            "name": "string",
            "description": "string",
            "acceptance_criteria": ["string"]
        }
    ],
    "tech_stack": ["string"],
    "folder_structure": {
        "folder_name": {
            "subfolders": {},
            "files": [
                {
                    "name": "string",
                    "type": "class|function|component",
                    "description": "string",
                    "properties": ["string"],
                    "methods": [
                        {
                            "name": "string",
                            "params": ["string"],
                            "return_type": "string",
                            "description": "string"
                        }
                    ]
                }
            ]
        }
    }
}
```
