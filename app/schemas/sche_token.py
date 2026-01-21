from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    is_first_login: bool = False


class TokenPayload(BaseModel):
    user_id: Optional[str] = None
