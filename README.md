# 键盘宏 (Keyboard Macro)

> Windows 桌面键盘宏工具 — 录制、回放、管理你的键盘操作

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)

## 简介

键盘宏是一款 Windows 桌面应用程序，能够录制用户的键盘操作并精确回放。支持多宏方案管理、速度调节、循环回放、全局热键控制和系统托盘后台运行。适用于重复性键盘操作自动化场景。

## 功能特性

### 键盘输入记录
- 实时捕获所有键盘按键（按下/释放），记录精确时间间隔（毫秒级）
- 支持组合键操作记录
- 基于 **Scan Code**（硬件扫描码）存储，**多键盘布局兼容**（中文/英文/日文等布局切换不影响录制和回放）

### 按键回放
- 按原始时间间隔精确回放
- 速度倍率：`0.25x` / `0.5x` / `1x` / `2x` / `3x` / `5x` / `10x`
- 多线程回放，不阻塞 UI，支持即时停止

### 宏管理
- 保存多个宏方案，支持命名、描述、编辑、删除
- JSON 格式导入/导出，方便分享和备份
- 自动持久化到 `~/.keyboard_macro/macros/`

### 全局热键控制

| 操作 | 热键 |
|------|------|
| 开始录制 | `Ctrl+Shift+F7` |
| 停止录制 | `Ctrl+Shift+F8` |
| 开始回放 | `Ctrl+Shift+F9` |
| 停止回放 | `Ctrl+Shift+F10` |

> 热键按键会自动从录制中过滤，避免冲突。

### 循环回放
- 单次回放 / 指定次数循环（1~9999）/ 无限循环模式

### 可视化界面
- 宏列表：名称、按键数、时长、循环次数一目了然
- 按键时间轴预览：可视化按键时间线，颜色分类区分按键类型
- 录制/回放实时状态指示和进度条

### 系统托盘
- 最小化到托盘后台运行
- 双击托盘图标恢复窗口
- 右键菜单快速操作（录制/回放/退出）
- 托盘气泡通知

## 快速开始

### 方式一：使用预编译 EXE（推荐）

从 [Releases 页面](https://github.com/zzxx223/keyboard-macro/releases) 下载 `KeyboardMacro.exe`，双击运行即可（会自动请求管理员权限）。

### 方式二：从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/zzxx223/keyboard-macro.git
cd keyboard-macro

# 2. 创建虚拟环境并安装依赖
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. 运行（需要管理员权限）
python main.py
```

或直接双击 `run.bat`（自动请求提权）。

### 从源码构建 EXE

```bash
# 1. 安装打包工具
pip install pyinstaller

# 2. 生成应用图标（需要 PyQt5）
python gen_icon.py

# 3. 构建 EXE
pyinstaller KeyboardMacro.spec --clean --noconfirm
# 生成的 EXE 在 dist/ 目录下
```

## 使用流程

```
┌─────────────────────────────────────────────────────┐
│  1. 按 Ctrl+Shift+F7 开始录制                        │
│  2. 执行你想要自动化的键盘操作                         │
│  3. 按 Ctrl+Shift+F8 停止录制                        │
│  4. 在列表中选中宏，调整速度和循环次数                   │
│  5. 按 Ctrl+Shift+F9 开始回放                        │
│  6. 按 Ctrl+Shift+F10 停止回放                       │
│  7. 关闭窗口 → 自动最小化到系统托盘                     │
└─────────────────────────────────────────────────────┘
```

## 项目结构

```
keyboard-macro/
├── main.py                  # 应用入口
├── run.bat                  # Windows 启动脚本（自动提权）
├── requirements.txt         # Python 依赖
├── KeyboardMacro.spec       # PyInstaller 打包配置
├── gen_icon.py              # 应用图标生成脚本（生成 app_icon.ico）
├── LICENSE                  # MIT 许可证
├── core/                    # 核心逻辑
│   ├── macro.py             # 数据模型 + 宏管理器（JSON 持久化）
│   ├── recorder.py          # 键盘录制引擎（keyboard.hook + Scan Code）
│   ├── player.py            # 键盘回放引擎（多线程 + 速度控制 + 循环）
│   └── hotkeys.py           # 全局热键管理器（冲突过滤）
└── ui/                      # 用户界面
    ├── main_window.py       # 主窗口（工具栏 + 宏列表 + 详情 + 时间轴）
    ├── timeline.py          # 按键时间轴可视化组件
    └── tray.py              # 系统托盘（图标 + 菜单 + 通知）
```

## 宏文件格式（JSON）

```json
{
  "format_version": "1.0",
  "macro": {
    "name": "MyMacro",
    "events": [
      {
        "key_name": "shift",
        "scan_code": 42,
        "event_type": "down",
        "timestamp": 0.0,
        "is_modifier": true
      },
      {
        "key_name": "a",
        "scan_code": 30,
        "event_type": "down",
        "timestamp": 0.05,
        "is_modifier": false
      }
    ],
    "created_at": 1719999999.0,
    "description": "示例宏",
    "loop_count": 1,
    "playback_speed": 1.0
  }
}
```

## 关键技术决策

| 决策 | 原因 |
|------|------|
| **PyQt5** | 成熟稳定的 GUI 框架，原生 Windows 外观，社区支持丰富 |
| **keyboard 库** | 低级键盘钩子，支持全局热键和按键模拟，跨布局兼容 |
| **Scan Code 存储** | 硬件扫描码不受键盘布局影响，确保录制和回放一致性 |
| **多线程回放** | 回放在独立线程执行，不阻塞 UI，支持即时停止 |
| **可中断睡眠** | 回放延迟使用增量检测（50ms 步进），确保停止响应迅速 |

## 系统要求

- **操作系统**：Windows 10 及以上
- **权限**：管理员权限（键盘钩子需要）
- **Python**：3.8+（仅从源码运行时需要）

## 技术栈

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — GUI 框架
- [keyboard](https://github.com/boppreh/keyboard) — 键盘钩子库
- [PyInstaller](https://pyinstaller.org/) — 打包工具

## 许可证

[MIT License](LICENSE) — 自由使用、修改、分发，请保留版权声明。

## 贡献

欢迎提交 Issue 和 Pull Request！
