from pydantic import BaseModel, EmailStr, Field
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    preferred_language: str = "en"
class LoginIn(BaseModel): email: EmailStr; password: str
class TicketIn(BaseModel):
    recipient: str = ""
    domain: str = "general"
    source_language: str
    target_language: str
    description: str = Field(default="", max_length=2000)
class TicketDecision(BaseModel):
    decision: str
    agent_id: int | None = None
class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    source_language: str
    target_language: str
    domain: str = "general"
    context: list[dict] = Field(default_factory=list, max_length=4)
