# Claude Repository Creator

Claude Repository Creator is an advanced AI-powered tool designed to streamline the process of creating and managing software projects. By leveraging the capabilities of Claude AI, this application automates the generation of project requirements, code, and documentation, making it easier for developers to kickstart their projects.

## Key Features

1. **AI-Driven Requirements Generation**: Automatically generate detailed project requirements based on user input, using both structured (JSON) and unstructured (text) formats.

2. **Intelligent Code Generation**: Create code for various programming languages and frameworks based on the generated requirements.

3. **Project Structure Creation**: Automatically set up a logical folder structure for your project, including necessary configuration files like .gitignore.

4. **Version Control Integration**: Built-in support for Git and Mercurial, allowing for easy project initialization and management.

5. **Iterative Development**: Support for updating and refining requirements and code based on user feedback.

6. **Multi-Language Support**: Generate code for multiple programming languages and frameworks, including Python, JavaScript, Java, React, and more.

7. **Comprehensive Documentation**: Automatically generate README files and other necessary documentation for your project.

8. **Custom Prompts**: Use markdown files in the prompts directory to create and use custom prompts for various stages of project creation.

## Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/Ono-Katsuki/Claude-Repository-Creator.git
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   - Create a `config.json` file in the root directory
   - Add your Claude and OpenAI API keys:
     ```json
     {
       "claude_api_key": "your_claude_api_key_here",
       "openai_api_key": "your_openai_api_key_here"
     }
     ```

4. Run the main script:
   ```
   python main.py
   ```

5. Follow the interactive prompts to create or update your project.

## Usage

The Claude Repository Creator offers an interactive command-line interface that guides you through the process of creating or updating a software project. Here's a brief overview of the main functionalities:

1. **Generate a New Project**: Provide a project description, and the tool will generate detailed requirements, create a project structure, and generate initial code.

2. **Continue from a Stage**: Pick up where you left off by selecting a specific stage in the project creation process.

3. **Update API Keys**: Easily update your Claude or OpenAI API keys within the application.

4. **Iterative Development**: Refine your project by updating requirements or regenerating code based on new input.

5. **Custom Prompts**: Create and use custom prompts for different stages of project creation.

### Using Custom Prompts

You can create and use custom prompts to tailor the project creation process to your specific needs:

1. Navigate to the `prompts` directory in the project folder.
2. Create a new markdown file (`.md`) in the appropriate subdirectory (e.g., `create_code_generation_prompt` for code generation prompts).
3. Write your custom prompt in the markdown file, using placeholders for dynamic content (e.g., `{tech_stack}`, `{features}`).
4. When running the tool, you'll be given the option to select from available prompts, including your custom ones.

This feature allows you to fine-tune the AI's output for different aspects of your project, such as requirements gathering, code generation, or documentation creation.

### Project and Requirements Generation

The tool generates various files and directories during the project creation process. Here's where you can find the generated content:

1. **Project Files**: 
   - Location: `claude_projects/<project_name>/v<timestamp>/`
   - Description: This directory contains the actual project files, including the generated code, README, and other project-specific files.

2. **Requirements Files**:
   - Text Requirements:
     - Location: `claude_projects/information_management/requirements/<project_name>/`
     - Format: `requirements_v<version_number>.txt`
   - JSON Requirements:
     - Location: `claude_projects/information_management/cache/<project_name>/`
     - Format: `requirements_v<version_number>.json`

3. **Project Summaries**:
   - Location: `claude_projects/information_management/markdown/<project_name>/`
   - Format: `<project_name>_summary_v<version_number>.md`
   - Description: These files contain comprehensive summaries of the project, including requirements, features, and generated code.

4. **Temporary Projects**:
   - During the initial stages of project creation, you might see temporary project folders named `temp_project_<timestamp>`. These are renamed to the actual project name once the project details are finalized.

Each time you update or regenerate your project, a new version is created, allowing you to track changes and iterations over time.

## Contributing

We welcome contributions to the Claude Repository Creator! Please feel free to submit issues, fork the repository and send pull requests!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool uses AI to generate code and project structures. While it aims to produce high-quality output, it's important to review and test all generated code before using it in production environments.
