from pydantic import BaseModel, Field


class PoolClaimRequest(BaseModel):
    staff_id: str | None = Field(default=None, description="Current staff id")


class PoolAssignRequest(BaseModel):
    lead_ids: list[str] = Field(min_length=1)
    staff_id: str = Field(description="Target staff id")


class PoolLeadOut(BaseModel):
    id: str
    name: str
    phone: str
    source: str
    dropReasonType: str
    dropReasonDetail: str
    dropTime: str | None = None
    originalOwner: str | None = None


class PoolListData(BaseModel):
    list: list[PoolLeadOut]
    total: int


class PoolClaimData(BaseModel):
    leadId: str
    claimer: str


class PoolAssignData(BaseModel):
    leadIds: list[str]
    assignee: str
    count: int


class PoolDeleteData(BaseModel):
    leadId: str


class PoolBatchDeleteRequest(BaseModel):
    lead_ids: list[str] = Field(min_length=1)


class PoolBatchDeleteData(BaseModel):
    leadIds: list[str]
    count: int


class PoolTransferOut(BaseModel):
    id: int
    leadId: str
    action: str
    fromOwnerId: str | None = None
    toOwnerId: str | None = None
    operatorStaffId: str
    note: str | None = None
    createdAt: str


class PoolTransferListData(BaseModel):
    list: list[PoolTransferOut]
    total: int
