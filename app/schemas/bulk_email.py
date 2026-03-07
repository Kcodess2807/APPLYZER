from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class BulkEmailRequest(BaseModel):
    recipients: List[str]
    subject: str
    body: str


class BulkEmailResponse(BaseModel):
    success: bool
    total: int
    sent: int
    failed: int
    results: Optional[List[Dict[str, Any]]] = []
    errors: Optional[List[Dict[str, Any]]] = []
