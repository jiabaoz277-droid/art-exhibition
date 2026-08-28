"""Pydantic 输入输出结构。"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    deadline: Optional[datetime] = None
    image_formats: str = "jpg,jpeg,png,webp"
    max_image_mb: float = 10.0


class CampaignOut(BaseModel):
    id: int
    title: str
    description: str
    deadline: Optional[datetime]
    image_formats: str
    max_image_mb: float
    link_token: str
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    admin_key: str = ""


class SQLQuery(BaseModel):
    sql: str


class QueryRequest(BaseModel):
    question: str


class CheckReportOut(BaseModel):
    missing: List[str] = []
    format_issues: List[str] = []
    notes: str = ""
