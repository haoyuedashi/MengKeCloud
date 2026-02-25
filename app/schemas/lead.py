from datetime import datetime
import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings


CHINESE_NAME_REGEX = re.compile(r"^[\u4e00-\u9fa5·]{1,3}$")
ENGLISH_NAME_REGEX = re.compile(r"^[A-Za-z][A-Za-z\s'.-]{0,19}$")


def _validate_lead_name(value: str) -> str:
    name = value.strip()
    if CHINESE_NAME_REGEX.fullmatch(name) or ENGLISH_NAME_REGEX.fullmatch(name):
        return name
    raise ValueError("客户姓名仅支持中文(最多3字)或英文(最多20字符)")


class LeadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=1, max_length=32)
    project: str = Field(min_length=1, max_length=128)
    source: str = Field(min_length=1, max_length=64)
    status: str = Field(min_length=1, max_length=64)
    level: str = Field(min_length=1, max_length=64)
    owner: str | None = Field(default=None, max_length=32)
    tags: list[str] = Field(default_factory=list)
    dynamic_data: dict[str, Any] = Field(default_factory=dict, alias="dynamicData")
    last_follow_up: datetime | None = Field(default=None, alias="lastFollowUp")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _validate_lead_name(value)


class LeadUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    phone: str | None = None
    project: str | None = None
    source: str | None = None
    status: str | None = None
    level: str | None = None
    owner: str | None = None
    tags: list[str] | None = None
    dynamic_data: dict[str, Any] | None = Field(default=None, alias="dynamicData")
    last_follow_up: datetime | None = Field(default=None, alias="lastFollowUp")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_lead_name(value)


class FollowUpCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(default="call")
    content: str
    operator: str
    timestamp: datetime | None = None
    audio_url: str | None = Field(default=None, alias="audioUrl")
    ai_analysis: dict[str, Any] | None = Field(default=None, alias="aiAnalysis")

    @field_validator("ai_analysis")
    @classmethod
    def validate_ai_analysis_size(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        payload_size = len(json.dumps(value, ensure_ascii=False))
        if payload_size > settings.ai_max_input_chars * 3:
            raise ValueError("AI分析内容过长，请缩短后重试")
        return value


class FollowUpRecordOut(BaseModel):
    id: int
    leadId: str
    type: str
    content: str
    operator: str
    timestamp: str
    audioUrl: str | None = None
    aiAnalysis: dict[str, Any] | None = None


class FollowUpAiSuggestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_goal: str | None = Field(default=None, alias="userGoal", max_length=200)


class FollowUpAiSuggestionData(BaseModel):
    nextSentence: str
    nextAction: str
    riskPoints: list[str]
    recommendedScript: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    model: str
    generatedAt: str


class LeadOut(BaseModel):
    id: str
    name: str
    phone: str
    project: str
    source: str
    status: str
    level: str
    owner: str | None = None
    createdAt: str | None = None
    lastFollowUp: str | None = None
    tags: list[str]
    dynamicData: dict[str, Any]


class LeadListData(BaseModel):
    list: list[LeadOut]
    total: int


class LeadDetailData(BaseModel):
    lead: LeadOut
    timeline: list[FollowUpRecordOut]


class LeadDeleteData(BaseModel):
    leadId: str


class LeadAssignRequest(BaseModel):
    leadIds: list[str] = Field(min_length=1)
    staffId: str = Field(min_length=1, max_length=32)


class LeadAssignData(BaseModel):
    leadIds: list[str]
    staffId: str
    count: int


class LeadToPoolRequest(BaseModel):
    leadIds: list[str] = Field(min_length=1)


class LeadToPoolData(BaseModel):
    leadIds: list[str]
    count: int


class LeadImportData(BaseModel):
    total: int
    success: int
    failed: int
    errors: list[str]


class AssignableStaffOut(BaseModel):
    id: str
    name: str
    deptName: str | None = None


class AssignableStaffData(BaseModel):
    list: list[AssignableStaffOut]
