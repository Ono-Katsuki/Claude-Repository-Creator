Generate a comprehensive and detailed requirements definition document based on the user's brief request. The output should be in the following JSON format:

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
        "name": "string",
        "subfolders": [
            {
                "name": "string",
                "subfolders": [],
                "files": []
            }
        ],
        "files": [
            {
                "name": "string",
                "content": {
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
            }
        ]
    }
}
```

## Guidelines
1. Accuracy: Ensure all information is based on the user's request or widely accepted best practices.
2. Completeness: Provide a comprehensive set of features and technical details.
3. Consistency: Maintain coherence across all sections of the document.
4. Future-oriented: Consider scalability and potential future enhancements.
5. Clarity: Use clear and concise language in all descriptions.

## Instructions for Each Section

1. project_name:
   - Provide a concise, descriptive name for the project.

2. description:
   - Write a brief overview of the project, its goals, and its main features.

3. features:
   - List all major features of the project.
   - For each feature, provide:
     - A clear, concise name
     - A detailed description
     - Specific, measurable acceptance criteria

4. tech_stack:
   - List all major technologies, frameworks, and tools required for the project.
   - Consider both frontend and backend technologies.
   - Include database systems, cloud services, and any other relevant technologies.

5. folder_structure:
   - Design a logical and efficient folder structure for the project.
   - Include all major directories and subdirectories.
   - For each file:
     - Provide a descriptive name
     - Specify the type (class, function, or component)
     - Give a brief description of its purpose
     - List its main properties and methods (if applicable)
     - For methods, include name, parameters, return type, and a brief description

## Additional Instructions
- Ensure the structure is scalable and follows best practices for the chosen tech stack.
- Consider security, performance, and maintainability in your design.
- Include necessary configurations, test files, and documentation in the folder structure.
- For complex features, break them down into smaller, manageable sub-features.
- Ensure that the folder structure and file contents align with the described features.

Generate the structured requirements definition based on these guidelines, ensuring each section is thoroughly detailed and aligned with modern software development practices.
