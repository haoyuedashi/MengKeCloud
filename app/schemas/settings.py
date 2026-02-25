from pydantic import BaseModel, ConfigDict, Field


class PlatformSettingsData(BaseModel):
    companyName: str
    officialPhone: str
    announcement: str
    annualTarget: int
    monthlyTargets: list[int]
    maxLeadsPerRep: int
    globalDropWarningDays: int
    aiEnabled: bool
    aiApiKeyMasked: str
    aiBaseUrl: str
    aiModel: str
    aiTimeoutSeconds: int


class PlatformSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    companyName: str = Field(min_length=1, max_length=128)
    officialPhone: str = Field(default="", max_length=64)
    announcement: str = Field(default="", max_length=500)
    annualTarget: int = Field(ge=0)
    monthlyTargets: list[int] = Field(min_length=12, max_length=12)
    maxLeadsPerRep: int = Field(ge=1, le=5000)
    globalDropWarningDays: int = Field(ge=1, le=30)
    aiEnabled: bool = False
    aiApiKey: str | None = Field(default=None, max_length=255)
    aiBaseUrl: str = Field(default="https://api.openai.com/v1", max_length=255)
    aiModel: str = Field(default="gpt-4o-mini", max_length=128)
    aiTimeoutSeconds: int = Field(default=12, ge=3, le=60)


class PlatformAiTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aiEnabled: bool = False
    aiApiKey: str | None = Field(default=None, max_length=255)
    aiBaseUrl: str = Field(default="https://api.openai.com/v1", max_length=255)
    aiModel: str = Field(default="gpt-4o-mini", max_length=128)
    aiTimeoutSeconds: int = Field(default=12, ge=3, le=60)


class PlatformAiTestData(BaseModel):
    ok: bool
    message: str
    latencyMs: int
    model: str


class DepartmentOut(BaseModel):
    id: int
    label: str
    parentId: int | None = None
    leaderStaffId: str | None = None
    leaderName: str | None = None
    sortOrder: int
    active: bool
    monthlyTarget: int


class DepartmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=128)
    leaderStaffId: str = Field(min_length=1, max_length=32)
    parentId: int | None = None
    sortOrder: int = 0
    active: bool = True
    monthlyTarget: int = Field(default=0, ge=0, le=10000)


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, min_length=1, max_length=128)
    leaderStaffId: str | None = Field(default=None, min_length=1, max_length=32)
    parentId: int | None = None
    sortOrder: int | None = None
    active: bool | None = None
    monthlyTarget: int | None = Field(default=None, ge=0, le=10000)


class OrgUserOut(BaseModel):
    id: str
    deptId: int | None = None
    name: str
    phone: str
    role: str
    active: bool
    joinDate: str
    monthlyTarget: int


class OrgUserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deptId: int | None = None
    name: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=1, max_length=32)
    role: str = Field(min_length=1, max_length=32)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    active: bool = True
    monthlyTarget: int = Field(default=0, ge=0, le=10000)


class OrgUserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deptId: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=64)
    phone: str | None = Field(default=None, min_length=1, max_length=32)
    role: str | None = Field(default=None, min_length=1, max_length=32)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    active: bool | None = None
    monthlyTarget: int | None = Field(default=None, ge=0, le=10000)


class OrgData(BaseModel):
    departments: list[DepartmentOut]
    users: list[OrgUserOut]


class RoleOut(BaseModel):
    id: int
    name: str
    isSystem: bool
    menuKeys: list[int]
    dataScope: str
    active: bool


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    menuKeys: list[int] = Field(default_factory=list)
    dataScope: str = Field(default="self", pattern="^(all|dept|self)$")
    active: bool = True


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    menuKeys: list[int] | None = None
    dataScope: str | None = Field(default=None, pattern="^(all|dept|self)$")
    active: bool | None = None


class RolesData(BaseModel):
    list: list[RoleOut]


class CustomFieldOut(BaseModel):
    id: int
    name: str
    code: str
    type: str
    placeholder: str
    isRequired: bool
    active: bool
    isSystem: bool
    sort: int
    fieldOptions: list[dict[str, str]]


class CustomFieldCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z_][a-z0-9_]*$")
    type: str = Field(pattern="^(text|textarea|number|select|date)$")
    placeholder: str = Field(default="", max_length=255)
    fieldOptions: list[dict[str, str]] = Field(default_factory=list)
    isRequired: bool = False
    active: bool = True
    sort: int | None = None


class CustomFieldUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    placeholder: str | None = Field(default=None, max_length=255)
    fieldOptions: list[dict[str, str]] | None = None
    isRequired: bool | None = None
    active: bool | None = None
    sort: int | None = None


class CustomFieldsData(BaseModel):
    entity: str
    list: list[CustomFieldOut]


class DictTypeOut(BaseModel):
    code: str
    name: str


class DictItemManageOut(BaseModel):
    id: int
    label: str
    value: str
    color: str | None = None
    active: bool
    isSystem: bool
    sort: int


class DictItemsManageData(BaseModel):
    dictType: str
    items: list[DictItemManageOut]


class DictItemManageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=32)
    active: bool = True


class DictItemManageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, min_length=1, max_length=128)
    value: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=32)
    active: bool | None = None


class DictItemMove(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: str = Field(pattern="^(up|down)$")


class RuleItem(BaseModel):
    active: bool
    days: int | None = None
    count: int | None = None
    protectHighIntent: bool | None = None


class RuleNotify(BaseModel):
    beforeDrop: bool
    afterDrop: bool


class RecycleRulesData(BaseModel):
    enabled: bool
    rule1: RuleItem
    rule2: RuleItem
    rule3: RuleItem
    notify: RuleNotify


class RecycleRulesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    rule1: RuleItem
    rule2: RuleItem
    rule3: RuleItem
    notify: RuleNotify
