from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class UserBaseSchema(BaseModel):

    id: UUID | None = None
    first_name: str = Field(
        ..., description="The first name of the user", examples=["John"]
    )
    last_name: str = Field(..., description="The last name of the user", examples=["Doe"])
    address: str | None = None
    activated: bool = False
    createdAt: datetime | None = None
    updatedAt: datetime | None = None

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True


class Status(Enum):
    Success = "Success"
    Failed = "Failed"


class UserResponse(BaseModel):
    Status: Status
    User: UserBaseSchema


class GetUserResponse(BaseModel):
    Status: Status
    User: UserBaseSchema


class ListUserResponse(BaseModel):
    status: Status
    results: int
    users: List[UserBaseSchema]


class DeleteUserResponse(BaseModel):
    Status: Status
    Message: str


class ActivityLogCreateSchema(BaseModel):
    user_id: UUID = Field(
        ..., description="The user ID this activity belongs to",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
    )
    action: str = Field(
        ..., description="The action performed", examples=["login"],
        min_length=1, max_length=100
    )
    description: Optional[str] = Field(
        None, description="Detailed description of the activity",
        examples=["User logged in from web browser"]
    )
    ip_address: Optional[str] = Field(
        None, description="IP address of the client", examples=["192.168.1.1"]
    )

    @field_validator("action")
    @classmethod
    def action_must_be_lowercase(cls, v):
        return v.lower()

    @field_validator("ip_address")
    @classmethod
    def validate_ip_format(cls, v):
        if v is None:
            return v
        parts = v.split(".")
        if len(parts) != 4:
            raise ValueError("IP address must have 4 octets")
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                raise ValueError("Each octet must be between 0 and 255")
        return v

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "action": "login",
                "description": "User logged in from web browser",
                "ip_address": "192.168.1.1"
            }
        }


class ActivityLogResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    createdAt: datetime | None = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ActivityLogResponse(BaseModel):
    Status: Status
    Log: ActivityLogResponseSchema


class ListActivityLogResponse(BaseModel):
    status: Status
    results: int
    logs: List[ActivityLogResponseSchema]


class ExternalHealthResponse(BaseModel):
    url: str = Field(..., examples=["https://httpbin.org/get"])
    status_code: int = Field(..., examples=[200])
    redirected: bool = Field(..., examples=[False])
    response_time_ms: float = Field(..., examples=[150.5])

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://httpbin.org/get",
                "status_code": 200,
                "redirected": False,
                "response_time_ms": 150.5
            }
        }
