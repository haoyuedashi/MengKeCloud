from pydantic import BaseModel, Field


class DashboardTrendValue(BaseModel):
    value: int
    trend: float


class DashboardStats(BaseModel):
    todayNewLeads: DashboardTrendValue
    weekFollowUps: DashboardTrendValue
    monthSigned: DashboardTrendValue


class DashboardTodoItem(BaseModel):
    leadId: str
    name: str
    level: str
    summary: str


class DashboardPoolWarning(BaseModel):
    leadId: str
    name: str
    daysOverdue: int = Field(ge=0)


class DashboardGoalProgress(BaseModel):
    current: int
    target: int
    percent: int = Field(ge=0, le=100)


class DashboardPerformance(BaseModel):
    followUp: DashboardGoalProgress
    signed: DashboardGoalProgress
    personalSigned: DashboardGoalProgress | None = None
    departmentSigned: DashboardGoalProgress | None = None


class DashboardOverviewData(BaseModel):
    stats: DashboardStats
    todoList: list[DashboardTodoItem]
    poolWarnings: list[DashboardPoolWarning]
    performance: DashboardPerformance
    announcement: str = ""
