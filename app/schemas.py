from pydantic import BaseModel, EmailStr, Field, field_validator


class ContactIn(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    phone: str | None = None
    industry: str | None = None
    budget: str | None = None
    service_interest: str | None = None
    message: str = Field(min_length=1)

    @field_validator("phone", "industry", "budget", "service_interest", mode="before")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value.strip() if isinstance(value, str) else value
