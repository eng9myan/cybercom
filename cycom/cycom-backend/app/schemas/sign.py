from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class SignTemplateBase(BaseModel):
    name: str
    fields_config: List[Dict[str, Any]]

class SignTemplateCreate(SignTemplateBase):
    pass

class SignTemplateResponse(SignTemplateBase):
    id: int
    file_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SignRequestCreate(BaseModel):
    template_id: int
    signers: List[Dict[str, Any]]

class SignRequestResponse(BaseModel):
    id: int
    template_id: int
    token: str
    status: str
    signers: List[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True
