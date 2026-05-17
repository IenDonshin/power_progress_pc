# POWER PROGRESS

这是一个自我引导程序，用来拆分任务，及时反馈，以增强“过程感”，培养人的执行力

这个程序像会兼有to do list, 日程表以及倒数日等程序的部分功能。

## 当前功能

- 动态倒数日：通过日历选择目标日期后，程序会刷新为 `3D 4H 20M` 这样的格式
- 可选时间：不设置具体时间时默认为 `00:00`，需要具体时间时可通过时钟拖动时针和分针选择
- 本地保存：倒数日数据会保存到 Windows 的 `%APPDATA%\PowerProgressPC\countdowns.json`
- 过期显示：超过目标时间后继续显示已过去的天、小时和分钟

## 运行方式

需要 Windows 上已安装 Python 3.10 或更高版本。

```powershell
python -m power_progress.app
```

## 测试

```powershell
python -m unittest discover -s tests
```
