from ninja import Schema

class LoginIn(Schema):
    username: str
    password: str

class RefreshIn(Schema):
    refresh: str

class TokenOut(Schema):
    access: str
    refresh: str
    token_type: str = "bearer"

class MeOut(Schema):
    id: int
    username: str
    role: str

class ProfileOut(Schema):
    id: int
    username: str
    role: str

class ChangePasswordIn(Schema):
    old_password: str
    new_password: str