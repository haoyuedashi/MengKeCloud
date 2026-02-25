from pydantic import BaseModel, ConfigDict, Field


class NotificationItem(BaseModel):
    id: int
    title: str
    content: str
    category: str
    isRead: bool
    createdAt: str | None = None
    readAt: str | None = None


class NotificationsData(BaseModel):
    list: list[NotificationItem]
    total: int


class NotificationReadAllData(BaseModel):
    updatedCount: int


class RecycleRunResult(BaseModel):
    recycledCount: int
    beforeNotifiedCount: int
    afterNotifiedCount: int


class NotificationReadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = Field(default=True)
