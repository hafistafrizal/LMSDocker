# courses/schemas.py
from datetime import datetime
from ninja import Schema

class CourseIn(Schema):
    code: str
    title: str
    description: str = ""
    teacher_id: int
    is_published: bool = False

class CoursePatch(Schema):
    code: str | None = None
    title: str | None = None
    description: str | None = None
    teacher_id: int | None = None
    is_published: bool | None = None
    
class CourseOut(Schema):
    id: int
    code: str
    title: str
    description: str
    teacher_id: int
    is_published: bool
    created_at: datetime

class Message(Schema):
    detail: str
