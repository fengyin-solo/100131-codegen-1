"""厂站信息业务规则：运行状态流转、资料变更约束、编号查重与流转留痕都收在这里。

运行状态只能沿固定顺序流转：
待投运 → 正常运行 → 停运检修（可恢复运行 / 退回待投运 / 退役）。
每次状态流转或资料变更都会追加一条带时间与经办人的历史记录，
已退役的厂站视为归档，任何动作与资料修改都会被拒绝。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.store import store

MODULE = "plank"

# 登记时必填，缺一项都不保存，并向前端说明缺的是哪一项。
REQUIRED_FIELDS = ["厂站编号", "厂站名称", "设计规模"]
# 厂站资料的可维护字段（厂站编号创建后不可改，不在编辑范围内）。
EDITABLE_FIELDS = ["厂站名称", "设计规模", "排放标准", "处理工艺", "服务区域", "投运日期"]
ALL_FIELDS = ["厂站编号", *EDITABLE_FIELDS]

STATUS_PENDING = "待投运"
STATUS_RUNNING = "正常运行"
STATUS_OVERHAUL = "停运检修"
STATUS_RETIRED = "已退役"
STATUS_ORDER = [STATUS_PENDING, STATUS_RUNNING, STATUS_OVERHAUL, STATUS_RETIRED]

# 这两个字段属于工艺核心资料，要改必须先把厂站退回待投运。
PROCESS_FIELDS = ["处理工艺", "服务区域"]

# (当前状态, 动作) -> 目标状态。不在表里的组合一律拒绝，保证只能逐步流转。
ALLOWED_TRANSITIONS: dict[tuple[str, str], str] = {
    (STATUS_PENDING, "投运"): STATUS_RUNNING,
    (STATUS_RUNNING, "停运检修"): STATUS_OVERHAUL,
    (STATUS_OVERHAUL, "恢复运行"): STATUS_RUNNING,
    (STATUS_RUNNING, "退回待投运"): STATUS_PENDING,
    (STATUS_OVERHAUL, "退回待投运"): STATUS_PENDING,
    (STATUS_RUNNING, "退役"): STATUS_RETIRED,
    (STATUS_OVERHAUL, "退役"): STATUS_RETIRED,
}
# 这些动作必须写清原因，否则不执行。
REASON_REQUIRED_ACTIONS = {"退回待投运"}

# 看板口径：还在流程上等处理的状态。
PENDING_STATUSES = {STATUS_PENDING, STATUS_OVERHAUL}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _clean(values: dict[str, Any], field: str) -> str:
    return str(values.get(field) or "").strip()


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

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def create_entry(
        self,
        values: dict[str, Any],
        operator: str,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str]:
        """登记新厂站：必填字段齐全、厂站编号不重复才落库，并写入第一条留痕。"""
        missing = [field for field in REQUIRED_FIELDS if not _clean(values, field)]
        if missing:
            return None, f"缺少必填字段：{'、'.join(missing)}，请补充后再保存"
        if not operator:
            return None, "经办人不能为空，无法登记厂站"

        code = _clean(values, "厂站编号")
        duplicate = next(
            (row for row in store.rows(MODULE) if str(row.get("厂站编号", "")).strip() == code),
            None,
        )
        if duplicate is not None:
            return None, f"厂站编号「{code}」已登记（序号 {duplicate.get('id')}），同一编号不能重复登记"

        rows = store.rows(MODULE)
        entry: dict[str, Any] = {
            "id": max((int(row.get("id", 0)) for row in rows), default=0) + 1,
        }
        for field in ALL_FIELDS:
            entry[field] = _clean(values, field)
        entry["status"] = STATUS_PENDING
        entry["运行状态"] = STATUS_PENDING
        entry["pending"] = True
        entry["abnormal"] = False
        entry["history"] = []
        self._record(entry, "登记", "", STATUS_PENDING, operator, reason or "")
        rows.append(entry)
        return entry, f"厂站「{code}」已登记，当前状态：{STATUS_PENDING}"

    def run_action(
        self,
        entry_id: int,
        action: str,
        operator: str,
        reason: str | None = None,
    ) -> tuple[dict[str, Any] | None, str]:
        """执行一次状态流转；来源状态、动作、原因任一不合规都会被拦下。"""
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"厂站 {entry_id} 不存在或已归档"
        if not operator:
            return None, "经办人不能为空，流转不会生效"

        current = str(entry.get("status", ""))
        if current == STATUS_RETIRED:
            return None, f"厂站「{entry.get('厂站编号')}」已退役归档，不能再做任何变更"
        target = ALLOWED_TRANSITIONS.get((current, action))
        if target is None:
            if action in {act for (_, act) in ALLOWED_TRANSITIONS}:
                return None, f"当前状态「{current}」下不能执行「{action}」，请按顺序流转"
            return None, f"动作「{action}」不属于厂站运行状态可执行范围"

        reason = (reason or "").strip()
        if action in REASON_REQUIRED_ACTIONS and not reason:
            return None, f"执行「{action}」必须写清退回原因，请补充后再提交"

        entry["status"] = target
        self._record(entry, action, current, target, operator, reason)
        self._refresh_flags(entry)
        return entry, f"厂站「{entry.get('厂站编号')}」已{action}：{current} → {target}"

    def update_fields(
        self,
        entry_id: int,
        values: dict[str, Any],
        operator: str,
    ) -> tuple[dict[str, Any] | None, str]:
        """修改厂站资料。

        - 已退役的厂站一律不可改；
        - 厂站编号不可修改；
        - 处理工艺、服务区域只有在待投运状态下允许变更，其他状态必须先退回待投运；
        - 设计规模不允许清空；
        - 变更同样留痕，记录改动前后的值。
        """
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"厂站 {entry_id} 不存在或已归档"
        if not operator:
            return None, "经办人不能为空，资料修改不会生效"
        current = str(entry.get("status", ""))
        if current == STATUS_RETIRED:
            return None, f"厂站「{entry.get('厂站编号')}」已退役归档，资料不能再改动"

        new_code = _clean(values, "厂站编号")
        if new_code and new_code != str(entry.get("厂站编号", "")).strip():
            return None, "厂站编号是唯一标识，创建后不能修改"

        if "设计规模" in values and not _clean(values, "设计规模"):
            return None, "缺少必填字段：设计规模，请补充后再保存"

        changes: list[str] = []
        for field in EDITABLE_FIELDS:
            if field not in values:
                continue
            new_value = _clean(values, field)
            old_value = str(entry.get(field, "") or "")
            if new_value == old_value:
                continue
            if field in PROCESS_FIELDS and current != STATUS_PENDING:
                return None, (
                    f"当前状态为「{current}」，{field}不能直接修改；"
                    "请先执行「退回待投运」并写明原因，再调整该字段"
                )
            changes.append(f"{field}：{old_value or '空'} → {new_value or '空'}")
            entry[field] = new_value

        if not changes:
            return entry, "资料没有变化，未生成变更记录"
        self._record(entry, "资料变更", current, current, operator, "；".join(changes))
        self._refresh_flags(entry)
        return entry, f"厂站「{entry.get('厂站编号')}」资料已更新，变更 {len(changes)} 项"

    def _refresh_flags(self, entry: dict[str, Any]) -> None:
        status = str(entry.get("status", ""))
        entry["运行状态"] = status
        entry["pending"] = status in PENDING_STATUSES
        entry["abnormal"] = status == STATUS_OVERHAUL

    def _record(
        self,
        entry: dict[str, Any],
        action: str,
        from_status: str,
        to_status: str,
        operator: str,
        reason: str,
    ) -> None:
        history = entry.setdefault("history", [])
        record = {
            "seq": len(history) + 1,
            "time": _now(),
            "operator": operator,
            "action": action,
            "from": from_status,
            "to": to_status,
            "reason": reason or "",
        }
        history.append(record)
        # 最近一次处理的信息直接挂在记录上，列表页与刷新后都能看到上一步经办人。
        entry["最近动作"] = action
        entry["最近经办人"] = operator
        entry["最近时间"] = record["time"]
        entry["运行状态"] = entry.get("status", to_status)
