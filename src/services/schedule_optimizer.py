"""智能时间块分配器"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import uuid

from src.models.task import Task, Priority
from src.models.time_block import TimeBlock, BlockType


class ScheduleOptimizer:
    """智能时间块分配器"""

    # 优先级分数
    PRIORITY_SCORE = {
        Priority.HIGH: 3,
        Priority.MEDIUM: 2,
        Priority.LOW: 1
    }

    # 黄金时间（上午精力充沛时段）
    GOLDEN_HOURS_START = 9
    GOLDEN_HOURS_END = 11

    @classmethod
    def allocate_time_blocks(
        cls,
        tasks: List[Task],
        work_start: datetime,
        work_end: datetime,
        break_interval: int = 90,
        break_duration: int = 15,
        lunch: Optional[Tuple[datetime, datetime]] = None
    ) -> List[TimeBlock]:
        """
        智能分配时间块

        Args:
            tasks: 任务列表
            work_start: 上班时间
            work_end: 下班时间
            break_interval: 休息间隔（分钟）
            break_duration: 休息时长（分钟）
            lunch: 午休区间 (开始, 结束)，为 None 表示不设午休；
                   落在午休区间的空档会被填成午休块，任务不会被排进去

        Returns:
            分配好的时间块数组
        """
        # 过滤掉已完成和没有预计时间的任务
        valid_tasks = [t for t in tasks if not t.completed and t.estimated_minutes > 0]

        if not valid_tasks:
            return []

        # 1. 分离高优先级任务和其他任务
        high_priority_tasks = [t for t in valid_tasks if t.priority == Priority.HIGH]
        other_tasks = [t for t in valid_tasks if t.priority != Priority.HIGH]

        # 2. 高优先级任务优先安排在黄金时间
        golden_tasks, remaining_tasks = cls._allocate_golden_time_tasks(
            high_priority_tasks, work_start, work_end
        )

        # 3. 按优先级和截止时间排序其他任务
        sorted_tasks = cls._sort_tasks(remaining_tasks + other_tasks)

        blocks = []
        current_time = work_start

        # 上班时间本身可能落在午休里（例如班次 09:30 而午休 09:30–12:00），
        # 先把开头的午休跳过去
        current_time = cls._skip_lunch(current_time, blocks, lunch)

        # 4. 安排黄金时间任务
        # 用 while 而非 for：撞上午休时需要「跳过午休后重排同一个任务」，
        # for 循环的 continue 会直接丢掉这个任务。
        index = 0
        while index < len(golden_tasks):
            task = golden_tasks[index]
            slot_end = cls._slot_end(current_time, work_end, lunch)

            block = cls._create_work_block(task, current_time)
            if block.end > slot_end:
                # 撞上午休：先跳过午休，下午重排这个任务，不截断也不丢弃
                if slot_end < work_end:
                    current_time = cls._skip_lunch(slot_end, blocks, lunch)
                    continue
                # 撞上下班：剩余不足 15 分钟就放弃
                if int((slot_end - current_time).total_seconds() / 60) < 15:
                    break
                block.end = slot_end

            blocks.append(block)
            current_time = cls._skip_lunch(block.end, blocks, lunch)
            index += 1

        # 5. 安排剩余任务
        # pending 可被就地摘除（填充任务），所以用下标循环而不是直接迭代
        pending = list(sorted_tasks)
        index = 0
        while index < len(pending):
            task = pending[index]
            slot_end = cls._slot_end(current_time, work_end, lunch)

            # 检查是否需要休息时间
            if cls._should_add_break(current_time, blocks, break_interval):
                available = int((slot_end - current_time).total_seconds() / 60)
                pause = min(break_duration, available)
                if pause >= 5:
                    break_block = cls._create_break_block(current_time, pause)
                    blocks.append(break_block)
                    current_time = cls._skip_lunch(break_block.end, blocks, lunch)
                    slot_end = cls._slot_end(current_time, work_end, lunch)

            # 创建工作块
            work_block = cls._create_work_block(task, current_time)

            # 检查是否超出可排班时间（下班前或午休开始前）
            if work_block.end > slot_end:
                # 撞上午休
                if slot_end < work_end:
                    # 午休后剩下的时间也排不下它，就截断到上午这段，
                    # 否则上午会整段空置；排得下才推到下午
                    afternoon_minutes = (work_end - lunch[1]).total_seconds() / 60
                    if task.estimated_minutes > afternoon_minutes:
                        before_lunch_minutes = int(
                            (slot_end - current_time).total_seconds() / 60)
                        if before_lunch_minutes >= 15:
                            work_block.end = slot_end
                            blocks.append(work_block)
                        break

                    # 上午空档里先看看有没有塞得下的任务
                    filler_idx = cls._find_filler(
                        pending, index + 1, slot_end - current_time)
                    if filler_idx is not None:
                        filler = cls._create_work_block(
                            pending[filler_idx], current_time)
                        blocks.append(filler)
                        pending.pop(filler_idx)
                        current_time = cls._skip_lunch(filler.end, blocks, lunch)
                        continue

                    # 都没有就跳过午休，下午重排当前任务
                    current_time = cls._skip_lunch(slot_end, blocks, lunch)
                    continue

                # 撞上下班：剩余时间够就截断，不够就放弃这个任务
                remaining_minutes = int((slot_end - current_time).total_seconds() / 60)
                if remaining_minutes >= 15:
                    work_block.end = slot_end
                    blocks.append(work_block)
                break

            blocks.append(work_block)
            current_time = cls._skip_lunch(work_block.end, blocks, lunch)
            index += 1

        return blocks

    @classmethod
    def _find_filler(cls, tasks: List[Task], start_index: int,
                     available: timedelta) -> Optional[int]:
        """
        在尚未排入的任务里找一个能塞进剩余时间的，返回它的下标。

        采用「最贴合」策略：优先选时长最接近剩余时间的，避免留下碎片。
        """
        minutes = available.total_seconds() / 60
        if minutes <= 0:
            return None

        best = None
        for i in range(start_index, len(tasks)):
            if tasks[i].estimated_minutes <= minutes:
                if best is None or (tasks[i].estimated_minutes
                                    > tasks[best].estimated_minutes):
                    best = i
        return best

    @classmethod
    def _slot_end(cls, current_time: datetime, work_end: datetime,
                  lunch: Optional[Tuple[datetime, datetime]]) -> datetime:
        """当前可排班到的时间点（午休开始时间会提前截断）"""
        if lunch and current_time < lunch[0] < work_end:
            return lunch[0]
        return work_end

    @classmethod
    def _skip_lunch(cls, current_time: datetime, blocks: List[TimeBlock],
                    lunch: Optional[Tuple[datetime, datetime]]) -> datetime:
        """若 current_time 落在午休区间内，插入午休块并跳到午休结束"""
        if not lunch:
            return current_time

        lunch_start, lunch_end = lunch
        if current_time < lunch_start or current_time >= lunch_end:
            return current_time

        blocks.append(cls._create_lunch_block(current_time, lunch_end))
        return lunch_end

    @classmethod
    def _allocate_golden_time_tasks(
        cls,
        tasks: List[Task],
        work_start: datetime,
        work_end: datetime
    ) -> tuple:
        """
        分配黄金时间任务

        Args:
            tasks: 高优先级任务列表
            work_start: 上班时间
            work_end: 下班时间

        Returns:
            (黄金时间任务, 剩余任务)
        """
        golden_start = work_start.replace(
            hour=cls.GOLDEN_HOURS_START,
            minute=0,
            second=0,
            microsecond=0
        ) if work_start.hour < cls.GOLDEN_HOURS_START else work_start

        golden_end = work_start.replace(
            hour=cls.GOLDEN_HOURS_END,
            minute=0,
            second=0,
            microsecond=0
        )

        if golden_end > work_end:
            golden_end = work_end

        golden_time_minutes = int((golden_end - golden_start).total_seconds() / 60)

        golden_tasks = []
        remaining_tasks = []
        used_minutes = 0

        # 按优先级排序
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                -cls.PRIORITY_SCORE[t.priority],
                t.deadline if t.deadline else datetime.max,
                t.estimated_minutes
            )
        )

        for task in sorted_tasks:
            if used_minutes + task.estimated_minutes <= golden_time_minutes:
                golden_tasks.append(task)
                used_minutes += task.estimated_minutes
            else:
                remaining_tasks.append(task)

        return golden_tasks, remaining_tasks

    @classmethod
    def _sort_tasks(cls, tasks: List[Task]) -> List[Task]:
        """排序任务：优先级 > deadline > 预计时长"""
        return sorted(
            tasks,
            key=lambda t: (
                -cls.PRIORITY_SCORE[t.priority],
                t.deadline if t.deadline else datetime.max,
                t.estimated_minutes
            )
        )

    @classmethod
    def _should_add_break(
        cls,
        current_time: datetime,
        blocks: List[TimeBlock],
        interval_minutes: int
    ) -> bool:
        """检查是否应该添加休息时间"""
        if not blocks:
            return False

        # 找到上一个工作块
        last_work_block = None
        for block in reversed(blocks):
            if block.type == BlockType.WORK:
                last_work_block = block
                break

        if not last_work_block:
            return False

        # 刚午休完是新的工作时段，不需要立刻再插一个休息
        if blocks[-1].type == BlockType.LUNCH:
            return False

        # 计算从上一个工作块开始到现在的时间
        elapsed_minutes = (current_time - last_work_block.start).total_seconds() / 60

        return elapsed_minutes >= interval_minutes

    @classmethod
    def _create_break_block(cls, start_time: datetime, duration: int = 15) -> TimeBlock:
        """创建休息时间块"""
        return TimeBlock(
            id=f"break-{uuid.uuid4().hex[:8]}",
            start=start_time,
            end=start_time + timedelta(minutes=duration),
            type=BlockType.BREAK,
            description="休息时间"
        )

    @classmethod
    def _create_lunch_block(cls, start_time: datetime, end_time: datetime) -> TimeBlock:
        """创建午休时间块"""
        return TimeBlock(
            id=f"lunch-{uuid.uuid4().hex[:8]}",
            start=start_time,
            end=end_time,
            type=BlockType.LUNCH,
            description="午休"
        )

    @classmethod
    def _create_work_block(cls, task: Task, start_time: datetime) -> TimeBlock:
        """创建工作块"""
        return TimeBlock(
            id=task.id,
            start=start_time,
            end=start_time + timedelta(minutes=task.estimated_minutes),
            task_id=task.id,
            type=BlockType.WORK,
            description=task.title
        )

    @classmethod
    def get_current_block(
        cls,
        blocks: List[TimeBlock]
    ) -> Optional[TimeBlock]:
        """
        获取当前时间块

        Args:
            blocks: 时间块列表

        Returns:
            当前时间块，如果没有则返回None
        """
        now = datetime.now()

        for block in blocks:
            if block.start <= now <= block.end:
                return block

        return None

    @classmethod
    def get_upcoming_blocks(
        cls,
        blocks: List[TimeBlock],
        count: int = 3
    ) -> List[TimeBlock]:
        """
        获取即将到来的时间块

        Args:
            blocks: 时间块列表
            count: 获取数量

        Returns:
            即将到来的时间块列表
        """
        now = datetime.now()
        upcoming = [b for b in blocks if b.start > now]
        return sorted(upcoming, key=lambda b: b.start)[:count]
