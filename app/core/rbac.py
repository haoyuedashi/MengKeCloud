from typing import Final


CANONICAL_ROLES: Final[set[str]] = {"admin", "manager", "sales"}

ROLE_ALIASES: Final[dict[str, str]] = {
    "admin": "admin",
    "administrator": "admin",
    "管理员": "admin",
    "超级管理员": "admin",
    "manager": "manager",
    "主管": "manager",
    "销售主管": "manager",
    "sales": "sales",
    "普通销售": "sales",
    "员工": "sales",
}


def normalize_role(role: str | None) -> str:
    role_text = (role or "").strip().lower()
    return ROLE_ALIASES.get(role_text, role_text)
