Generate complete code for a {language} file based on the following information:
{feature_info}
File Information:
Name: {file_name}
Type: {file_content.type}
Description: {file_content.description}
Properties: {', '.join(file_content.properties)}
Methods:
{format_methods(file_content.methods)}
Important Instructions:
1. Generate ONLY the complete code without any explanations, placeholders, or TODOs.
2. Include ALL specified properties and methods.
3. Implement the full logic for the feature.
4. Include error handling where necessary.
5. Do NOT include any comments in the code unless they are crucial for understanding.
6. Do NOT use ellipsis (...) or placeholders like "// Implementation here".
7. Ensure the code is production-ready and follows best practices for {language}.
8. For HTML, provide the complete structure; for CSS, include all relevant styles.
9. For React or similar frameworks, include full state management and lifecycle methods as necessary.
10. Absolutely avoid hallucinations.
Output the complete code directly without any markdown formatting or code blocks.
