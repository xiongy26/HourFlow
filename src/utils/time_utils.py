"""时间工具函数"""
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple


def format_countdown(seconds: int, show_seconds: bool = False) -> str:
    """
    格式化倒计时显示

    Args:
        seconds: 秒数
        show_seconds: 是否显示秒数，默认False不显示

    Returns:
        格式化的字符串 "时:分" 或 "时:分:秒"
    """
    if seconds <= 0:
        return "00:00" if not show_seconds else "00:00:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if show_seconds:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}"


def _at(now: datetime, time_str: str) -> datetime:
    """把 "HH:MM" 解析成 now 所在当天的 datetime"""
    hour, minute = map(int, time_str.split(':'))
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _overlap_seconds(a_start: datetime, a_end: datetime,
                     b_start: datetime, b_end: datetime) -> float:
    """两个时间区间的重叠秒数（无重叠返回 0）"""
    lo = max(a_start, b_start)
    hi = min(a_end, b_end)
    return max((hi - lo).total_seconds(), 0.0)


def get_lunch_window(now: datetime, window_start: datetime, window_end: datetime,
                  lunch_break_enabled: bool,
                  lunch_break_start: str, lunch_break_end: str
                  ) -> Optional[Tuple[datetime, datetime]]:
    """
    计算午休区间与给定时间窗口的交集。

    午休配置可能落在工作时段之外（例如班次 09:00–12:00 而午休仍是 12:00–13:30），
    直接按配置时长扣减会算出负的总工时，所以这里先裁剪到窗口内。
    午休未启用、结束早于开始或与窗口无交集时返回 None。
    """
    if not lunch_break_enabled:
        return None

    lunch_start = _at(now, lunch_break_start)
    lunch_end = _at(now, lunch_break_end)
    if lunch_end <= lunch_start:
        return None

    lo = max(lunch_start, window_start)
    hi = min(lunch_end, window_end)
    if hi <= lo:
        return None
    return lo, hi


def calculate_work_progress(
    work_start_time: str,
    work_end_time: str,
    lunch_break_enabled: bool = True,
    lunch_break_start: str = "12:00",
    lunch_break_end: str = "13:30"
) -> float:
    """
    计算工作时间进度百分比（排除午休时间）

    午休期间进度保持不变：午休中已经流逝的那部分会从已工作时长中扣除。

    Args:
        work_start_time: 上班时间 "HH:MM"
        work_end_time: 下班时间 "HH:MM"
        lunch_break_enabled: 是否启用午休
        lunch_break_start: 午休开始时间 "HH:MM"
        lunch_break_end: 午休结束时间 "HH:MM"

    Returns:
        进度百分比 (0-100)
    """
    now = datetime.now()

    start = _at(now, work_start_time)
    end = _at(now, work_end_time)

    # 如果还未到上班时间
    if now < start:
        return 0.0

    # 如果已经过了下班时间
    if now >= end:
        return 100.0

    # 总工作时长（秒）
    total_work_seconds = (end - start).total_seconds()

    # 已工作时间（秒）
    elapsed_seconds = (now - start).total_seconds()

    # 启用午休时：总时长扣掉整段午休，已工作时长扣掉「午休中已流逝」的部分
    lunch = get_lunch_window(now, start, end, lunch_break_enabled,
                          lunch_break_start, lunch_break_end)
    if lunch:
        total_work_seconds -= (lunch[1] - lunch[0]).total_seconds()
        elapsed_seconds -= _overlap_seconds(start, now, lunch[0], lunch[1])

    if total_work_seconds <= 0:
        return 0.0

    progress = (elapsed_seconds / total_work_seconds) * 100
    return round(min(max(progress, 0.0), 100.0), 1)


def calculate_time_remaining(
    work_end_hour: int,
    work_end_minute: int = 0,
    lunch_break_enabled: bool = True,
    lunch_break_start: str = "12:00",
    lunch_break_end: str = "13:30"
) -> int:
    """
    计算距离下班的时间（秒），考虑午休时间

    午休期间剩余工时保持不变：午休中尚未消耗的部分不计入剩余工时。

    Args:
        work_end_hour: 下班小时（24小时制）
        work_end_minute: 下班分钟
        lunch_break_enabled: 是否启用午休
        lunch_break_start: 午休开始时间 "HH:MM"
        lunch_break_end: 午休结束时间 "HH:MM"

    Returns:
        剩余秒数
    """
    now = datetime.now()
    end_time = now.replace(
        hour=work_end_hour,
        minute=work_end_minute,
        second=0,
        microsecond=0
    )

    # 如果已经过了下班时间，返回0
    if now >= end_time:
        return 0

    remaining = (end_time - now).total_seconds()

    # 剩余工时 = 到下班的时长 - 尚未消耗的午休时长（午休中则只扣剩下的那段）
    lunch = get_lunch_window(now, now, end_time, lunch_break_enabled,
                          lunch_break_start, lunch_break_end)
    if lunch:
        remaining -= (lunch[1] - lunch[0]).total_seconds()

    return max(int(remaining), 0)


def is_workday(work_days: List[int]) -> bool:
    """
    检查当前是否是工作日

    Args:
        work_days: 工作日列表 [1,2,3,4,5] 1=周一, 7=周日

    Returns:
        是否是工作日
    """
    # datetime.weekday() 返回 0-6，0=周一，6=周日
    # 转换为 1=周一，7=周日
    today = datetime.now().weekday() + 1
    return today in work_days


def get_time_period() -> str:
    """
    获取当前时间段

    Returns:
        时间段名称：morning/afternoon/evening
    """
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"


def get_current_time_string() -> str:
    """
    获取当前时间字符串

    Returns:
        当前时间 "HH:MM:SS"
    """
    return datetime.now().strftime("%H:%M:%S")


def get_current_date_string() -> str:
    """
    获取当前日期字符串

    Returns:
        当前日期 "YYYY-MM-DD"
    """
    return datetime.now().strftime("%Y-%m-%d")


def parse_time_string(time_str: str) -> Tuple[int, int]:
    """
    解析时间字符串为小时和分钟

    Args:
        time_str: 时间字符串 "HH:MM"

    Returns:
        (小时, 分钟) 元组
    """
    parts = time_str.split(':')
    return int(parts[0]), int(parts[1])


def create_datetime_from_time(time_str: str) -> datetime:
    """
    从时间字符串创建当天的datetime

    Args:
        time_str: 时间字符串 "HH:MM"

    Returns:
        datetime对象
    """
    hour, minute = parse_time_string(time_str)
    now = datetime.now()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def format_time_range(start: Optional[datetime], end: Optional[datetime]) -> str:
    """
    格式化时间范围

    Args:
        start: 开始时间
        end: 结束时间

    Returns:
        格式化的字符串 "HH:MM - HH:MM"
    """
    if start is None or end is None:
        return ""
    return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"


def is_time_in_range(check_time: datetime, start: datetime, end: datetime) -> bool:
    """
    检查时间是否在范围内

    Args:
        check_time: 要检查的时间
        start: 开始时间
        end: 结束时间

    Returns:
        是否在范围内
    """
    return start <= check_time <= end


def get_time_until(target_hour: int, target_minute: int = 0) -> timedelta:
    """
    获取到目标时间的差值

    Args:
        target_hour: 目标小时
        target_minute: 目标分钟

    Returns:
        时间差
    """
    now = datetime.now()
    target = now.replace(
        hour=target_hour,
        minute=target_minute,
        second=0,
        microsecond=0
    )

    if now >= target:
        # 如果已经过了目标时间，返回0
        return timedelta(0)

    return target - now


def get_weekday_name(weekday: int) -> str:
    """
    获取星期几的中文名称

    Args:
        weekday: 星期几 (1=周一, 7=周日)

    Returns:
        中文星期名称
    """
    names = {
        1: "周一",
        2: "周二",
        3: "周三",
        4: "周四",
        5: "周五",
        6: "周六",
        7: "周日"
    }
    return names.get(weekday, "")


def get_today_weekday() -> int:
    """
    获取今天是星期几

    Returns:
        星期几 (1=周一, 7=周日)
    """
    return datetime.now().weekday() + 1
