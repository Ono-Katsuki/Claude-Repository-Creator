from prompt_manager import PromptManager

prompt_manager = PromptManager()

def create_text_requirements_prompt(user_request):
    return prompt_manager.get_prompt('create_text_requirements_prompt', 'default', user_request=user_request)

def create_text_update_prompt(current_requirements, user_feedback):
    return prompt_manager.get_prompt('create_text_update_prompt', 'default', current_requirements=current_requirements, user_feedback=user_feedback)

def create_json_requirements_prompt(project_description):
    return prompt_manager.get_prompt('create_json_requirements_prompt', 'default', project_description=project_description)

def create_json_update_prompt(current_requirements, project_description, user_feedback):
    return prompt_manager.get_prompt('create_json_update_prompt', 'default', current_requirements=current_requirements, project_description=project_description, user_feedback=user_feedback)

def create_code_generation_prompt(feature, file_content, file_name, language):
    return prompt_manager.get_prompt('create_code_generation_prompt', 'default', feature=feature, file_content=file_content, file_name=file_name, language=language)

def create_code_generation_system_prompt(language):
    return prompt_manager.get_prompt('create_code_generation_system_prompt', 'default', language=language)
