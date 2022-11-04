from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemForm(BaseModel):
    """Форма для предствления элемента"""
    id: str
    url: Optional[str]
    parentId: Optional[str]
    size: Optional[int]
    type: str


class ImportForm(BaseModel):
    """Форма для предствления импорта"""
    items: list[ItemForm]
    updateDate: str = datetime.now().isoformat()
