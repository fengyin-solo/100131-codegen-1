"""厂站信息接口：维护污水处理厂，覆盖登记、状态流转、资料变更与流转记录查询。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.plank import PlankService

router = APIRouter(prefix="/api/plank", tags=["厂站信息"])

service = PlankService()

LIST_FIELDS = ["厂站编号", "厂站名称", "设计规模", "排放标准", "处理工艺", "服务区域", "投运日期", "运行状态"]
STATUSES = ["待投运", "正常运行", "停运检修", "已退役"]


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按厂站编号检索"),
    status: str | None = Query(default=None, description="待投运、正常运行、停运检修、已退役"),
    page: int = 1,
    size: int = 20,
) -> PageResult[dict]:
    """按厂站编号与状态过滤厂站信息列表；没有数据时返回空页，不报错。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/summary")
def status_summary() -> dict[str, int]:
    """按运行状态统计厂站数量，列表页统计卡片与表内数据同源。"""
    return service.status_summary()


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出厂站信息清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "plank", "total": total, "items": items}


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条污水处理厂明细（含流转记录）；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"污水处理厂 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条污水处理厂：缺必填项、厂站编号重复都会当场拦下并说明原因。"""
    entry, message = service.create_entry(payload.values)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message="污水处理厂已登记，初始状态为「待投运」", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条污水处理厂执行状态流转；不合规的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    operator = str(payload.values.get("经办人") or "").strip()
    reason = str(payload.values.get("原因") or payload.remark or "").strip()
    entry, message = service.run_action(entry_id, action, operator=operator, reason=reason)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)


@router.put("/{entry_id}", response_model=ActionResult)
def update_entry(entry_id: int, payload: EntryPayload) -> ActionResult:
    """修改处理工艺或服务区域：仅待投运状态可改，必须写清原因并记录经办人。"""
    operator = str(payload.values.get("经办人") or "").strip()
    reason = str(payload.values.get("原因") or payload.remark or "").strip()
    entry, message = service.update_entry(entry_id, payload.values, operator=operator, reason=reason)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
