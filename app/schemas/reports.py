from pydantic import BaseModel, Field


class TrendValue(BaseModel):
    value: int
    trend: float


class ReportsSummary(BaseModel):
    newLeads: TrendValue
    assignedLeads: TrendValue
    followUps: TrendValue
    signedLeads: TrendValue
    invitationRate: TrendValue
    visitRate: TrendValue


class TrendSeries(BaseModel):
    window: str
    xAxis: list[str]
    series: list[int]


class FunnelItem(BaseModel):
    name: str
    value: int


class LossItem(BaseModel):
    name: str
    value: int


class StaffRankingItem(BaseModel):
    staffId: str
    name: str
    newLeads: int
    followUps: int
    signed: int
    conversion: float = Field(ge=0)


class FilterOption(BaseModel):
    label: str
    value: str


class ReportsFiltersMeta(BaseModel):
    departments: list[FilterOption]
    staffs: list[FilterOption]


class PersonalGoalProgress(BaseModel):
    signedCurrent: int
    signedTarget: int
    signedPercent: int = Field(ge=0, le=100)


class ReportsOverviewData(BaseModel):
    summary: ReportsSummary
    trend: TrendSeries
    funnel: list[FunnelItem]
    loss: list[LossItem]
    staffRanking: list[StaffRankingItem]
    filtersMeta: ReportsFiltersMeta
    personalGoal: PersonalGoalProgress | None = None
