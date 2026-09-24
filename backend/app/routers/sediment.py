"""沉淀池管理接口：维护沉淀池，覆盖强制排泥、故障报修、排空清理等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.sediment import SedimentService

router = APIRouter(prefix="/api/sediment", tags=["沉淀池管理"])

service = SedimentService()

LIST_FIELDS = ["池编号", "所属厂站", "池容", "表面负荷", "污泥浓度", "排泥周期", "刮泥机状态", "沉淀池状态"]
STATUSES = ["正常", "泥位偏高", "刮泥故障", "待维修", "已排空"]


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按池编号检索"),
    status: str | None = Query(default=None, description="正常、泥位偏高、刮泥故障、待维修、已排空"),
    page: int = 1,
    size: int = 20,
) -> PageResult[dict]:
    """按池编号与状态过滤沉淀池管理列表；没有数据时返回空页，不报错。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条沉淀池明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"沉淀池 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条沉淀池，缺字段时说明原因而不是静默丢弃。"""
    entry, missing = service.create_entry(payload.values)
    if missing:
        return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
    return ActionResult(ok=True, message="沉淀池已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条沉淀池执行强制排泥、故障报修、排空清理；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出沉淀池管理清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "sediment", "total": total, "items": items}
