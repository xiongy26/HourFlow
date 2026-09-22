# WorkCountdown

> 您的桌面时间管理助手 | Your Desktop Time Management Assistant

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.6.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 项目简介
HourFlow 是一款专为上班族设计的桌面端时间管理工具，帮助用户建立明确的时间观念，提高工作效率。

### 核心价值

- ⏰ **时间可视化** - 实时显示下班倒计时，增强时间紧迫感
- 🧠 **智能规划** - 自动分配时间块，减少决策疲劳
- 🏃 **健康提醒** - 定时提醒久坐休息，保护身体健康
- 📊 **效率追踪** - 清晰展示任务进度和工作统计

## ✨ 功能特性

### 1. 下班倒计时 ⏰
- 实时显示距离下班剩余时间
- 周末/节假日自动切换显示模式
- 系统托盘实时显示剩余时间
- 支持自定义上下班时间

### 2. 智能时间块分配 📊
- 支持添加任务（标题、预计时长、优先级）
- 智能算法自动分配时间块
- 考虑优先级、黄金时间、连续性和休息时间
- 支持手动调整

### 3. 久坐提醒 🏃
- 可配置提醒间隔（默认 45 分钟）
- 系统原生通知 + 声音提醒
- 统计今日久坐时长和休息次数

### 4. 今日计划视图 📅
- 垂直时间轴布局
- 当前时间高亮显示
- 时间块颜色编码（工作/休息/会议）
- 点击查看任务详情

### 5. 时间感知增强 🎯
- 时间进度圆环（显示已过工作时间百分比）
- 时间流逝动画效果
- 配色随时间变化（早晨→中午→傍晚）

## 🛠️ 技术栈

| 技术 | 说明 |
|------|------|
| **Python 3.10+** | 编程语言 |
| **PySide6** | Qt 官方 Python 绑定，跨平台 GUI 框架 |
| **QSS** | Qt 样式表，类 CSS 语法 |
| **JSON** | 轻量级数据存储 |

## 📦 安装

### 环境要求

- Python 3.10 或更高版本
- Windows / macOS / Linux

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/workcountdown.git
cd workcountdown

# 2. 创建虚拟环境（推荐）
python -m venv .venv

# 3. 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行应用
python main.py
```

## 📁 项目结构

```
workcountdown/
├── main.py                      # 应用入口
├── requirements.txt             # Python 依赖
├── README.md                    # 项目说明
├── config.json                  # 默认配置
├── resources/                   # 资源文件
│   ├── icons/                   # 图标文件
│   └── styles/
│       └── style.qss            # QSS 样式文件
├── src/
│   ├── core/                    # 核心业务逻辑
│   │   ├── config_manager.py    # 配置管理器
│   │   └── task_manager.py      # 任务管理器
│   ├── models/                  # 数据模型
│   │   ├── task.py              # 任务模型
│   │   └── time_block.py        # 时间块模型
│   ├── services/                # 服务层
│   │   ├── schedule_optimizer.py # 时间块分配算法
│   │   └── reminder_service.py   # 久坐提醒服务
│   ├── ui/                      # UI 界面
│   │   ├── main_window.py       # 主窗口
│   │   └── widgets/             # 自定义组件
│   │       ├── countdown_widget.py    # 倒计时组件
│   │       ├── schedule_widget.py     # 今日计划组件
│   │       ├── time_viz_widget.py     # 时间可视化组件
│   │       ├── task_manager_widget.py # 任务管理组件
│   │       └── settings_dialog.py     # 设置对话框
│   └── utils/                   # 工具函数
│       ├── time_utils.py        # 时间工具函数
│       └── platform_utils.py    # 平台相关工具
└── tests/                       # 单元测试
```

## 🔧 配置

配置文件位于 `~/.workcountdown/config.json`

```json
{
    "work_start": "09:00",
    "work_end": "18:00",
    "work_days": [1, 2, 3, 4, 5],
    "break_interval": 45,
    "theme": "light"
}
```

## 📝 使用指南

### 首次使用
1. 运行应用后，点击设置图标配置您的上下班时间
2. 添加今日待办任务
3. 点击"优化安排"让 AI 智能分配时间块

### 日常使用
- 查看倒计时了解剩余工作时间
- 根据时间轴安排当日任务
- 注意久坐提醒，适当休息

## 🖥️ 系统要求

- **Windows**: Windows 10 或更高版本
- **macOS**: macOS 10.14 或更高版本
- **Linux**: Ubuntu 18.04 或更高版本

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 感谢

- [PySide6](https://www.qt.io/qt-for-python) - 强大的跨平台 GUI 框架
- 所有开源库的贡献者

---

*让时间成为你的朋友，而不是敌人*
