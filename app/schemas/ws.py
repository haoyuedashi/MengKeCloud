from pydantic import BaseModel, ConfigDict, Field


class VoiceAssistPublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(default="ai_hint")
    content: str = Field(min_length=1)


class VoiceAssistPublishData(BaseModel):
    channel: str
    staffId: str
    eventType: str
    version: str
