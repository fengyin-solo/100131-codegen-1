"""厂站信息业务规则：状态流转、字段校验与筛选口径都收在这里。

运行状态按「待投运 → 正常运行 → 停运检修」顺序流转，已退役为终态；
每次变更都写入流转记录（时间、经办人、原状态、新状态、原因），
交接班后刷新页面仍能追到上一步是谁处理的。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.store import store

MODULE = "plank"
REQUIRED_FIELDS = ["厂站编号", "厂站名称", "设计规模"]
EDITABLE_FIELDS = ["处理工艺", "服务区域"]
STATUS_ORDER = ["待投运", "正常运行", "停运检修", "已退役"]
TERMINAL_STATUS = "已退役"

# 每个动作允许的起始状态与目标状态；需要写清原因的动作单独标注。
ACTION_RULES: dict[str, dict[str, Any]] = {
    "申请投运": {"from": ["待投运"], "to": "正常运行"},
    "停运检修": {"from": ["正常运行"], "to": "停运检修"},
    "恢复运行": {"from": ["停运检修"], "to": "正常运行"},
    "退回待投运": {"from": ["正常运行", "停运检修"], "to": "待投运", "require_reason": True},
    "退役": {"from": ["待投运", "停运检修"], "to": "已退役"},
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _history_entry(
    *,
    action: str,
    operator: str,
    from_status: str,
    to_status: str,
    reason: str = "",
    content: str = "",
) -> dict[str, Any]:
    return {
        "时间": _now(),
        "经办人": operator,
        "动作": action,
        "原状态": from_status,
        "新状态": to_status,
        "原因": reason,
        "内容": content,
    }


class PlankService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("厂站编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def status_summary(self) -> dict[str, int]:
        """按运行状态统计厂站数量，给列表页的统计卡片用。"""
        summary = {status: 0 for status in STATUS_ORDER}
        for row in store.rows(MODULE):
            status = str(row.get("status", ""))
            if status in summary:
                summary[status] += 1
        return summary

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, f"缺少必填字段：{'、'.join(missing)}，未保存"
        operator = str(values.get("经办人") or "").strip()
        if not operator:
            return None, "缺少经办人，未保存"
        code = str(values.get("厂站编号") or "").strip()
        rows = store.rows(MODULE)
        if any(str(row.get("厂站编号", "")).strip() == code for row in rows):
            return None, f"厂站编号 {code} 已登记，不能重复登记"
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        for field in ["厂站编号", "厂站名称", "设计规模", "排放标准", "处理工艺", "服务区域", "投运日期"]:
            entry[field] = str(values.get(field) or "").strip()
        entry["status"] = STATUS_ORDER[0]
        entry["运行状态"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        entry["流转记录"] = [
            _history_entry(action="登记", operator=operator, from_status="", to_status=STATUS_ORDER[0])
        ]
        rows.append(entry)
        return entry, ""

    def run_action(
        self,
        entry_id: int,
        action: str,
        *,
        operator: str,
        reason: str = "",
    ) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"污水处理厂 {entry_id} 不存在或已归档"
        current = str(entry.get("status", ""))
        if current == TERMINAL_STATUS:
            return None, f"厂站已退役，不能再执行「{action}」"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于厂站信息可执行范围"
        rule = ACTION_RULES[action]
        if current not in rule["from"]:
            allowed = "、".join(rule["from"])
            return None, f"当前状态「{current}」不能执行「{action}」，仅「{allowed}」状态可执行"
        reason = reason.strip()
        if rule.get("require_reason") and not reason:
            return None, f"执行「{action}」必须写清原因"
        operator = operator.strip()
        if not operator:
            return None, "请填写经办人，再执行状态流转"
        target = str(rule["to"])
        entry["status"] = target
        entry["运行状态"] = target
        entry["pending"] = target in ("待投运", "停运检修")
        entry["abnormal"] = False
        entry.setdefault("流转记录", []).append(
            _history_entry(action=action, operator=operator, from_status=current, to_status=target, reason=reason)
        )
        return entry, f"污水处理厂已{action}，状态变为「{target}」"

    def update_entry(
        self,
        entry_id: int,
        values: dict[str, Any],
        *,
        operator: str,
        reason: str = "",
    ) -> tuple[dict[str, Any] | None, str]:
        """修改处理工艺、服务区域：必须先退回待投运，并写清原因留痕。"""
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"污水处理厂 {entry_id} 不存在或已归档"
        current = str(entry.get("status", ""))
        if current == TERMINAL_STATUS:
            return None, "厂站已退役，不能再改动处理工艺或服务区域"
        if current != STATUS_ORDER[0]:
            return None, f"当前状态「{current}」不能修改处理工艺或服务区域，请先退回待投运"
        reason = reason.strip()
        if not reason:
            return None, "修改处理工艺或服务区域必须写清原因"
        operator = operator.strip()
        if not operator:
            return None, "请填写经办人，再提交变更"
        changes: list[str] = []
        for field in EDITABLE_FIELDS:
            new_value = str(values.get(field) or "").strip()
            if not new_value:
                continue
            old_value = str(entry.get(field) or "").strip()
            if new_value != old_value:
                entry[field] = new_value
                changes.append(f"{field}：{old_value or '空'}→{new_value}")
        if not changes:
            return None, "处理工艺、服务区域没有实际变更内容，未保存"
        entry.setdefault("流转记录", []).append(
            _history_entry(
                action="资料变更",
                operator=operator,
                from_status=current,
                to_status=current,
                reason=reason,
                content="；".join(changes),
            )
        )
        return entry, f"厂站资料已变更（{'；'.join(changes)}）"
