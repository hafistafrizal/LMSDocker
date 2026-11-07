from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CourseIn(BaseModel):
    code: str
    title: str
    description: Optional[str] = ""
    is_published: bool = False


class CoursePatchIn(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_published: Optional[bool] = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    description: str
    is_published: bool
    teacher_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None