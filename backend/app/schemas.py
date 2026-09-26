"""接口出入参模型：列表分页、动作结果与各模块的明细结构。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    size: int = 20


class ActionResult(BaseModel):
    ok: bool
    message: str
    entry: dict[str, Any] | None = None


class EntryPayload(BaseModel):
    """登记或修改一条业务记录时提交的字段集合。"""

    values: dict[str, Any] = Field(default_factory=dict)
    remark: str | None = None
    operator: str | None = None  # 本次操作经办人，状态流转与资料变更必填
    reason: str | None = None  # 退回待投运等动作的原因



class PlankEntry(BaseModel):
    """污水处理厂明细结构。"""

    field_0: str | None = None  # 厂站编号
    field_1: str | None = None  # 厂站名称
    field_2: str | None = None  # 设计规模
    field_3: str | None = None  # 排放标准
    field_4: str | None = None  # 处理工艺
    field_5: str | None = None  # 服务区域
    field_6: str | None = None  # 投运日期
    field_7: str | None = None  # 运行状态

class InflowEntry(BaseModel):
    """进水记录明细结构。"""

    field_0: str | None = None  # 记录编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 监测时间
    field_3: str | None = None  # 进水量
    field_4: str | None = None  # COD浓度
    field_5: str | None = None  # 氨氮浓度
    field_6: str | None = None  # pH值
    field_7: str | None = None  # 进水状态

class AerationEntry(BaseModel):
    """曝气区段明细结构。"""

    field_0: str | None = None  # 区段编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 溶解氧目标
    field_3: str | None = None  # 风机频率
    field_4: str | None = None  # 曝气时长
    field_5: str | None = None  # 阀门开度
    field_6: str | None = None  # 运行电流
    field_7: str | None = None  # 曝气状态

class ChemicalEntry(BaseModel):
    """加药方案明细结构。"""

    field_0: str | None = None  # 方案编号
    field_1: str | None = None  # 药剂名称
    field_2: str | None = None  # 加药点位
    field_3: str | None = None  # 投加浓度
    field_4: str | None = None  # 投加流量
    field_5: str | None = None  # 药剂余量
    field_6: str | None = None  # 配药人员
    field_7: str | None = None  # 加药状态

class SedimentEntry(BaseModel):
    """沉淀池明细结构。"""

    field_0: str | None = None  # 池编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 池容
    field_3: str | None = None  # 表面负荷
    field_4: str | None = None  # 污泥浓度
    field_5: str | None = None  # 排泥周期
    field_6: str | None = None  # 刮泥机状态
    field_7: str | None = None  # 沉淀池状态

class SludgeEntry(BaseModel):
    """脱水机组明细结构。"""

    field_0: str | None = None  # 机组编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 机组类型
    field_3: str | None = None  # 进泥量
    field_4: str | None = None  # 出泥含水率
    field_5: str | None = None  # 絮凝剂用量
    field_6: str | None = None  # 运行功率
    field_7: str | None = None  # 机组状态

class EffluentEntry(BaseModel):
    """出水记录明细结构。"""

    field_0: str | None = None  # 记录编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 监测时间
    field_3: str | None = None  # COD出水值
    field_4: str | None = None  # 氨氮出水值
    field_5: str | None = None  # 总磷出水值
    field_6: str | None = None  # 排放流量
    field_7: str | None = None  # 出水状态

class LabtestEntry(BaseModel):
    """化验报告明细结构。"""

    field_0: str | None = None  # 报告编号
    field_1: str | None = None  # 取样点位
    field_2: str | None = None  # 化验项目
    field_3: str | None = None  # 分析方法
    field_4: str | None = None  # 化验结果
    field_5: str | None = None  # 化验人员
    field_6: str | None = None  # 取样日期
    field_7: str | None = None  # 报告状态

class ReagentEntry(BaseModel):
    """化验药剂明细结构。"""

    field_0: str | None = None  # 药剂编号
    field_1: str | None = None  # 药剂名称
    field_2: str | None = None  # 规格等级
    field_3: str | None = None  # 存放位置
    field_4: str | None = None  # 有效期至
    field_5: str | None = None  # 当前数量
    field_6: str | None = None  # 领用登记
    field_7: str | None = None  # 药剂状态

class EquipEntry(BaseModel):
    """维保记录明细结构。"""

    field_0: str | None = None  # 记录编号
    field_1: str | None = None  # 设备名称
    field_2: str | None = None  # 维保类型
    field_3: str | None = None  # 维保内容
    field_4: str | None = None  # 维保人员
    field_5: str | None = None  # 计划日期
    field_6: str | None = None  # 完成日期
    field_7: str | None = None  # 维保状态

class PumpEntry(BaseModel):
    """水泵机组明细结构。"""

    field_0: str | None = None  # 机组编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 水泵型号
    field_3: str | None = None  # 额定流量
    field_4: str | None = None  # 运行电流
    field_5: str | None = None  # 累计运行时间
    field_6: str | None = None  # 轴承温度
    field_7: str | None = None  # 机组状态

class PowerEntry(BaseModel):
    """能耗记录明细结构。"""

    field_0: str | None = None  # 记录编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 统计周期
    field_3: str | None = None  # 电耗总量
    field_4: str | None = None  # 药耗总量
    field_5: str | None = None  # 吨水电耗
    field_6: str | None = None  # 吨水药耗
    field_7: str | None = None  # 记录状态

class PipeEntry(BaseModel):
    """管网巡查明细结构。"""

    field_0: str | None = None  # 巡查编号
    field_1: str | None = None  # 巡查路段
    field_2: str | None = None  # 巡查人员
    field_3: str | None = None  # 巡查日期
    field_4: str | None = None  # 管线状况
    field_5: str | None = None  # 井盖状况
    field_6: str | None = None  # 异常描述
    field_7: str | None = None  # 巡查状态

class LiftEntry(BaseModel):
    """提升泵站明细结构。"""

    field_0: str | None = None  # 泵站编号
    field_1: str | None = None  # 泵站名称
    field_2: str | None = None  # 集水池容积
    field_3: str | None = None  # 扬程
    field_4: str | None = None  # 服务管网
    field_5: str | None = None  # 格栅状态
    field_6: str | None = None  # 液位高度
    field_7: str | None = None  # 泵站状态

class MeterEntry(BaseModel):
    """仪表明细结构。"""

    field_0: str | None = None  # 仪表编号
    field_1: str | None = None  # 仪表名称
    field_2: str | None = None  # 安装位置
    field_3: str | None = None  # 测量参数
    field_4: str | None = None  # 仪表量程
    field_5: str | None = None  # 最近校准日
    field_6: str | None = None  # 下次校准日
    field_7: str | None = None  # 仪表状态

class Dispatch2Entry(BaseModel):
    """调度指令明细结构。"""

    field_0: str | None = None  # 调度编号
    field_1: str | None = None  # 调度类型
    field_2: str | None = None  # 来源厂站
    field_3: str | None = None  # 目标厂站
    field_4: str | None = None  # 调度流量
    field_5: str | None = None  # 调度时段
    field_6: str | None = None  # 调度人员
    field_7: str | None = None  # 调度状态

class StormEntry(BaseModel):
    """雨水调控明细结构。"""

    field_0: str | None = None  # 调控编号
    field_1: str | None = None  # 所属厂站
    field_2: str | None = None  # 降雨强度
    field_3: str | None = None  # 截流倍数
    field_4: str | None = None  # 调蓄池液位
    field_5: str | None = None  # 溢流次数
    field_6: str | None = None  # 调控时段
    field_7: str | None = None  # 调控状态

class PollutantEntry(BaseModel):
    """溯源记录明细结构。"""

    field_0: str | None = None  # 溯源编号
    field_1: str | None = None  # 异常厂站
    field_2: str | None = None  # 异常指标
    field_3: str | None = None  # 疑似来源
    field_4: str | None = None  # 排查范围
    field_5: str | None = None  # 排查结果
    field_6: str | None = None  # 处置措施
    field_7: str | None = None  # 溯源状态

class MaterialEntry(BaseModel):
    """耗材明细结构。"""

    field_0: str | None = None  # 耗材编号
    field_1: str | None = None  # 耗材名称
    field_2: str | None = None  # 规格型号
    field_3: str | None = None  # 用途分类
    field_4: str | None = None  # 存放库房
    field_5: str | None = None  # 最低保有量
    field_6: str | None = None  # 当前存量
    field_7: str | None = None  # 耗材状态

class LicenseEntry(BaseModel):
    """排污许可证明细结构。"""

    field_0: str | None = None  # 证照编号
    field_1: str | None = None  # 持证单位
    field_2: str | None = None  # 许可排放量
    field_3: str | None = None  # 排放口编号
    field_4: str | None = None  # 发证机关
    field_5: str | None = None  # 有效起日
    field_6: str | None = None  # 有效止日
    field_7: str | None = None  # 证照状态
