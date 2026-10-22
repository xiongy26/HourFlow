"""时间块数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class BlockType(Enum):
    """时间块类型枚举"""
    WORK = "work"
    BREAK = "break"
    MEETING = "meeting"
    LUNCH = "lunch"

    @classmethod
    def from_string(cls, value: str) -> 'BlockType':
        """从字符串创建块类型"""
        value = value.lower()
        for item in cls:
            if item.value == value:
                return item
        return cls.WORK  # 默认工作块


@dataclass
class TimeBlock:
    """时间块模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    task_id: Optional[str] = None
    type: BlockType = BlockType.WORK
    description: str = ""

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.type, str):
            self.type = BlockType.from_string(self.type)
        if isinstance(self.start, str):
            self.start = datetime.fromisoformat(self.start)
        if isinstance(self.end, str):
            self.end = datetime.fromisoformat(self.end)

    @property
    def duration_minutes(self) -> int:
        """获取持续时间（分钟）"""
        if self.start and self.end:
            return int((self.end - self.start).total_seconds() / 60)
        return 0

    @property
    def duration_formatted(self) -> str:
        """获取格式化的时间长度"""
        minutes = self.duration_minutes
        if minutes < 60:
            return f"{minutes}分钟"
        hours = minutes // 60
        mins = minutes % 60
        if mins > 0:
            return f"{hours}小时{mins}分钟"
        return f"{hours}小时"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'start': self.start.isoformat() if self.start else None,
            'end': self.end.isoformat() if self.end else None,
            'task_id': self.task_id,
            'type': self.type.value,
            'description': self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TimeBlock':
        """从字典创建时间块"""
        # 处理 type
        block_type = data.get('type', 'work')
        if isinstance(block_type, str):
            block_type = BlockType.from_string(block_type)

        # 处理 start
        start = data.get('start')
        if isinstance(start, str):
            start = datetime.fromisoformat(start)

        # 处理 end
        end = data.get('end')
        if isinstance(end, str):
            end = datetime.fromisoformat(end)

        return cls(
            id=data.get('id', str(uuid.uuid4())),
            start=start,
            end=end,
            task_id=data.get('task_id'),
            type=block_type,
            description=data.get('description', ''),
        )
