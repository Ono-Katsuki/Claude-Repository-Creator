from typing import List, Optional
from pydantic import BaseModel, Field

class Method(BaseModel):
    name: str
    params: List[str]
    return_type: str
    description: str

class FileContent(BaseModel):
    type: str
    description: str
    properties: List[str] = Field(default_factory=list)
    methods: List[Method] = Field(default_factory=list)

class File(BaseModel):
    name: str
    content: FileContent

class Folder(BaseModel):
    name: str
    subfolders: List['Folder'] = Field(default_factory=list)
    files: List[File] = Field(default_factory=list)

class Feature(BaseModel):
    name: str
    description: str
    acceptance_criteria: List[str]

class Requirements(BaseModel):
    project_name: str
    description: str
    features: List[Feature]
    tech_stack: List[str]
    folder_structure: Folder

Folder.update_forward_refs()
