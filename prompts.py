def create_text_requirements_prompt(user_request):
    return f"""
    You are a skilled business analyst and system architect tasked with generating detailed software requirements from a user's brief request. Your goal is to expand on the user's initial idea and create a comprehensive set of requirements that cover various aspects of software development.

    Here's the user's request:
    <user_request>
    {user_request}
    </user_request>

    Based on this request, generate detailed requirements following these steps:

    1. Analyze the user request and identify the core functionality and purpose of the proposed software.

    2. Generate detailed requirements for each of the following categories. Ensure that each requirement is specific, measurable, achievable, relevant, and time-bound (SMART):

       a. Business Requirements:
          - Develop 3-5 specific use cases or user stories
          - Assign priority levels (High, Medium, Low) to each feature
          - Estimate expected user base and scale

       b. Technical Requirements:
          - Define performance requirements (e.g., response time, concurrent users)
          - Outline security requirements (e.g., authentication method, data encryption)
          - Specify scalability requirements

       c. Interface Design:
          - Describe key elements of the user interface
          - Suggest a color scheme and overall style guide
          - Outline the main screen flow

       d. Data Model:
          - List main entities and their relationships
          - Specify data types, constraints, and validation rules for key fields

       e. External System Integration:
          - Identify necessary external APIs or services
          - Suggest data synchronization frequency and methods

       f. Deployment Information:
          - Recommend suitable hosting environments
          - List required infrastructure components

       g. Testing Requirements:
          - Provide 3-5 key test scenarios
          - Suggest quality metrics (e.g., code coverage percentage)

       h. Internationalization and Localization:
          - List languages and regions to support
          - Specify date, time, and currency format requirements

       i. Accessibility Requirements:
          - Identify relevant accessibility guidelines to follow

       j. Legal Requirements:
          - Mention applicable data privacy regulations
          - Note any industry-specific compliance needs

    3. Pay special attention to use cases, data model, and UI/UX information, providing extra detail in these areas.

    4. Ensure all requirements are consistent with each other and the original user request.

    5. If any information is not explicitly mentioned or cannot be reasonably inferred from the user's request, make logical assumptions based on industry best practices. Clearly mark these assumptions.

    Present your detailed requirements in a structured format, using appropriate headings for each category. Use bullet points for individual requirements within each category. Begin your response with:

    <detailed_requirements>

    End your response with:

    </detailed_requirements>

    It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
    You need to think through every detail and edge case for each component:
    Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
    Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
    Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

    Remember to maintain a professional tone throughout the document and ensure that all requirements are clear, specific, and actionable.
    """

def create_text_update_prompt(current_requirements, user_feedback):
    return f"""
    You are tasked with updating and improving the following software requirements based on user feedback. Your goal is to incorporate the user's suggestions and address any concerns while maintaining the overall structure and completeness of the requirements.

    Current Requirements:
    <current_requirements>
    {current_requirements}
    </current_requirements>

    User Feedback:
    <user_feedback>
    {user_feedback}
    </user_feedback>

    Please update the requirements based on the user feedback. Consider the following guidelines:
    1. Address all points mentioned in the user feedback.
    2. Maintain the overall structure of the requirements.
    3. Ensure consistency between new and existing requirements.
    4. If the user feedback introduces new features or major changes, integrate them seamlessly into the existing structure.
    5. If the user feedback is vague or unclear, make reasonable assumptions and note them clearly.
    6. Maintain the SMART criteria for all requirements (Specific, Measurable, Achievable, Relevant, Time-bound).

    Present your updated requirements in the same structured format as the original, using appropriate headings for each category. Use bullet points for individual requirements within each category. Begin your response with:

    <detailed_requirements>

    End your response with:

    </detailed_requirements>

    It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
    You need to think through every detail and edge case for each component:
    Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
    Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
    Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

    Ensure that your updated requirements are comprehensive, clear, and actionable.
    """

def create_json_requirements_prompt(project_description):
    return f"""
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
    {{
        "project_name": "string",
        "description": "string",
        "features": [
            {{
                "name": "string",
                "description": "string",
                "acceptance_criteria": ["string"]
            }}
        ],
        "tech_stack": ["string"],
        "folder_structure": {{
            "folder_name": {{
                "subfolders": {{}},
                "files": [
                    {{
                        "name": "string",
                        "type": "class|function|component",
                        "description": "string",
                        "properties": ["string"],
                        "methods": [
                            {{
                                "name": "string",
                                "params": ["string"],
                                "return_type": "string",
                                "description": "string"
                            }}
                        ]
                    }}
                ]
            }}
        }}
    }}
    """

def create_json_update_prompt(current_requirements, project_description):
    return f"""
    Evaluate and improve the following project requirements:
    Provide the improved requirements in the same JSON format as the input.
    Produce only the JSON without any comments or additional text.
    It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.

    It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
    You need to think through every detail and edge case for each component:
    Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
    Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
    Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

    Project Description:
    {project_description}

    Current Requirements:
    {current_requirements}

    Please analyze these requirements and make the following improvements:
    1. Ensure there is a main file (e.g., main.py, index.js) in the appropriate location.
    2. Check that all necessary dependencies are included.
    3. Verify that the folder structure is logical and follows best practices for the chosen tech stack.
    4. Make sure all function and method calls are correct and consistent.
    5. Add any missing critical components for the project to function properly.
    6. Ensure the tech stack is appropriate for the project description.
    7. Verify that all features have clear and testable acceptance criteria.
    """

def create_json_completion_prompt(parsed_part, unparsed_part, project_description):
    return f"""
Project Description:
{project_description}

Based on the above project description and the following incomplete JSON, complete ONLY the missing part:

Parsed part (DO NOT modify or repeat this part):
{parsed_part}

Unparsed part (Complete from here):
{unparsed_part}

Instructions:
1. Generate ONLY the missing part of the JSON, starting from where the unparsed part begins.
2. Ensure the generated part is consistent with the structure and naming conventions in the parsed part.
3. DO NOT repeat any information already present in the parsed part.
4. The output should be a valid JSON fragment that, when combined with the parsed part, forms a complete and valid JSON object.
5. Make sure the completed JSON aligns with the project description and requirements.
6. DO NOT include any explanations, comments, or additional text. Provide ONLY the JSON fragment.

Remember:
- Include a main file (e.g., main.js, index.js) in the appropriate location if not already present.
- Ensure all necessary dependencies are included.
- Verify that the folder structure is logical and follows best practices for the chosen tech stack.
- Make sure all function and method calls are correct and consistent.
- Add any missing critical components for the project to function properly.
- Ensure the tech stack is appropriate for the project description.
- Verify that all features have clear and testable acceptance criteria.

IMPORTANT: Produce ONLY the JSON fragment for the missing part. DO NOT include any additional text, explanations, or the parsed part in your response.

Example input:
Parsed part:
{{
  "project_name": "Example Project",
  "description": "This is an example project description.",
  "features": [
    {{
      "name": "Feature 1",
      "description": "Description of Feature 1",
      "acceptance_criteria": [
        "Criterion 1",
        "Criterion 2"
      ]
    }}
  ],
  "tech_stack": [
    "Technology 1",
    "Technology 2"
  ],
  "folder_structure": {{
    "backend": {{
      "subfolders": {{
        "src": {{
          "subfolders": {{
            "controllers": {{
              "files": [
                {{
                  "name": "exampleController.js",
                  "type": "function",
                  "description": "Example controller",
                  "properties": [],
                  "methods": [
                    {{
                      "name": "exampleMethod",
                      "params": ["param1", "param2"],
                      "return_type": "object",
                      "description": "Example method description"
                    }}
                  ]
                }}
              ]
            }}
          }}
        }}
      }}
    }}
  }}
}}

Unparsed part:
,
    "frontend": {{
      "subfolders": {{
        "src": {{
          "subfolders": {{
            "components": {{
              "files": [
                {{
                  "name": "ExampleComponent.js",
                  "type": "component",
                  "description": "Example component",
                  "properties": ["exampleProp"],
                  "methods": [
                    {{
                      "name": "render",
                      "params": [],
                      "return_type": "JSX.Element",
                      "description": "Renders the component"
                    }}
                  ]
                }}
              ]
            }}
          }}
        }}
      }}
    }}
  }}

Example output:
,
    "frontend": {{
      "subfolders": {{
        "src": {{
          "subfolders": {{
            "components": {{
              "files": [
                {{
                  "name": "ExampleComponent.js",
                  "type": "component",
                  "description": "Example component",
                  "properties": ["exampleProp"],
                  "methods": [
                    {{
                      "name": "render",
                      "params": [],
                      "return_type": "JSX.Element",
                      "description": "Renders the component"
                    }}
                  ]
                }},
                {{
                  "name": "AnotherComponent.js",
                  "type": "component",
                  "description": "Another example component",
                  "properties": ["prop1", "prop2"],
                  "methods": [
                    {{
                      "name": "handleClick",
                      "params": ["event"],
                      "return_type": "void",
                      "description": "Handles click events"
                    }}
                  ]
                }}
              ]
            }},
            "utils": {{
              "files": [
                {{
                  "name": "helpers.js",
                  "type": "function",
                  "description": "Helper functions",
                  "properties": [],
                  "methods": [
                    {{
                      "name": "formatData",
                      "params": ["data"],
                      "return_type": "object",
                      "description": "Formats data for display"
                    }}
                  ]
                }}
              ]
            }}
          }},
          "files": [
            {{
              "name": "App.js",
              "type": "component",
              "description": "Root component of the application",
              "properties": [],
              "methods": [
                {{
                  "name": "render",
                  "params": [],
                  "return_type": "JSX.Element",
                  "description": "Renders the main application structure"
                }}
              ]
            }},
            {{
              "name": "index.js",
              "type": "function",
              "description": "Entry point of the application",
              "properties": [],
              "methods": [
                {{
                  "name": "render",
                  "params": [],
                  "return_type": "void",
                  "description": "Renders the app to the DOM"
                }}
              ]
            }}
          ]
        }}
      }}
    }}
  }}
"""
