<div align="center">

# Lunar Gap Fit

**用农历-公历日期漂移数据，看见每一年之间的时间差。**

**Study how a Gregorian date and its corresponding Chinese lunar date drift across years.**

[![Tests](https://github.com/Xhou-J/ri/actions/workflows/tests.yml/badge.svg)](https://github.com/Xhou-J/ri/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
![Calendar](https://img.shields.io/badge/calendar-HKO%201901--2100-blue)
![Interactive](https://img.shields.io/badge/output-interactive.html-6f42c1)

**中文：** [这是什么](#这是什么--what--why) · [安装](#安装--install) · [快速开始](#快速开始--quick-start) · [交互函数图](#交互函数图--interactive-graph) · [输出文件](#输出文件--outputs) · [准确性](#日历准确性--calendar-accuracy)

**EN:** [What](#这是什么--what--why) · [Install](#安装--install) · [Quick Start](#快速开始--quick-start) · [Interactive Graph](#交互函数图--interactive-graph) · [Outputs](#输出文件--outputs) · [Accuracy](#日历准确性--calendar-accuracy)

</div>

---

## 这是什么 · What & Why

| 中文 | English |
| --- | --- |
| Lunar Gap Fit 是一个轻量 Python 工具，用来研究某个公历日期与对应农历日期在 1901-2100 年之间如何漂移。 | Lunar Gap Fit is a lightweight Python tool for studying how a Gregorian date and its corresponding Chinese lunar date drift between 1901 and 2100. |
| 它会把每一年同一公历月日与匹配农历日期之间的差值做成序列，再用 Fourier 模型拟合这个序列。 | It builds a year-by-year day-gap sequence and fits that sequence with a Fourier model. |
| 你可以用它找出下一次“公历生日”和“农历生日”同一天出现的年份，也可以直接看交互式函数图。 | You can use it to find the next solar/lunar birthday coincidence, or inspect the fitted shape in an interactive graph. |

它适合回答这类问题：

- `2004-07-24` 对应的农历日期，在之后哪些年份会再次落到同一天？
- 某个公历月日和某个农历月日之间，每年的差值如何变化？
- 这个变化是否接近 19 年、38 年、76 年等周期？
- 不同日期对应的函数图形形状有什么差异？

It is useful for questions like:

- When will the lunar date corresponding to `2004-07-24` coincide with the same Gregorian date again?
- How does the gap between a chosen Gregorian month/day and a chosen lunar month/day change year by year?
- Does the pattern resemble a 19-year, 38-year, or 76-year rhythm?
- How does the fitted curve shape change when the selected date changes?

---

## 功能概览 · Features

| 中文 | English |
| --- | --- |
| 公历日期转农历日期 | Convert Gregorian dates to Chinese lunar dates |
| 生成 1901-2100 年逐年 gap 序列 | Generate 1901-2100 year-by-year gap data |
| 自动模式：输入一个公历日期，自动取对应农历锚点 | Auto mode: input one Gregorian date and derive the lunar anchor |
| 手动模式：指定公历月日和农历月日进行比较 | Manual mode: compare a chosen Gregorian month/day with a lunar month/day |
| 自动选择 Fourier 周期和谐波数 | Automatically select Fourier period and harmonic count |
| 默认生成离线 `interactive.html` 函数图 | Generate an offline `interactive.html` graph by default |
| 支持预测年份、查找下一次重合、生日模式 | Predict target years, find next coincidences, and run birthday helpers |
| 输出 CSV、JSON、Python 函数、PNG 图、Markdown 报告 | Export CSV, JSON, standalone Python formula, PNG plot, and Markdown report |

---

## 安装 · Install

```bash
git clone https://github.com/Xhou-J/ri.git
cd ri
pip install -e .
```

只安装依赖：

```bash
pip install -r requirements.txt
```

Install requirements only:

```bash
pip install -r requirements.txt
```

---

## 快速开始 · Quick Start

自动模式：输入一个公历日期。

Auto mode: input one Gregorian date.

```bash
python -m lunar_gap_fit 2004-07-24 --out out_2004_07_24
```

安装后也可以使用命令行入口：

After installation, the console command also works:

```bash
lunar-gap-fit 2004-07-24 --out out_2004_07_24
```

支持这些日期格式：

Supported date formats:

```text
YYYY-MM-DD
YYYY-M-D
YYYY/MM/DD
YYYY/M/D
YYYY.MM.DD
YYYY.M.D
```

示例 / Examples:

```bash
lunar-gap-fit 2008-07-10 --out out_2008_07_10
lunar-gap-fit 2008/7/10 --out out_2008_07_10
lunar-gap-fit 2008.7.10 --out out_2008_07_10
```

---

## 手动锚点模式 · Manual Anchor Mode

当你想比较一个指定公历月日和一个指定农历月日时，使用手动模式。

Use manual mode when you want to compare a chosen Gregorian month/day with a chosen lunar month/day.

示例：公历 5 月 8 日 vs 农历三月二十三。

Example: Gregorian May 8 vs lunar March 23.

```bash
lunar-gap-fit --solar 05-08 --lunar-month 3 --lunar-day 23 --out out_0508_lunar_0323
```

`--solar` 支持：

`--solar` accepts:

```text
MM-DD
M-D
MM/DD
M/D
MM.DD
M.DD
```

闰月示例 / Leap lunar month example:

```bash
lunar-gap-fit --solar 05-23 --lunar-month 4 --lunar-day 1 --lunar-leap --out out_leap_0401
```

---

## 匹配模式 · Matching Modes

默认模式会选择距离公历锚点最近的农历日期。

Default matching chooses the lunar date nearest to the Gregorian anchor.

```bash
lunar-gap-fit 2004-07-24
```

如果必须要求匹配的农历日期落在同一个公历年份内：

Force the matched lunar date to be inside the same Gregorian year:

```bash
lunar-gap-fit 2004-07-24 --match-same-gregorian-year
```

---

## 交互函数图 · Interactive Graph

默认情况下，每次正常运行都会生成 `interactive.html`。

Every normal run writes `interactive.html` by default.

```bash
lunar-gap-fit 2004-07-24 --no-plot --out out_2004_07_24
```

打开 `out_2004_07_24/interactive.html` 后，你会看到：

Open `out_2004_07_24/interactive.html` to inspect:

| 中文 | English |
| --- | --- |
| 上方：精细函数图、实际 gap 点、零线和拟合摘要 | Top: fitted curve, actual gap points, zero line, and fit summary |
| 下方：年份选择、每日滑块、缩放、横向平移 | Bottom: year selector, day slider, zoom, and horizontal pan |
| 默认中文界面，可切换英文 | Chinese UI by default, with English switching |
| 每次日期变化都会完整重新计算，不复用旧日期系数 | Every date change recomputes fully and never reuses another date's coefficients |
| Web Worker 后台计算，已完整算过的日期才进入 cache | A Web Worker computes in the background; cache stores only completed exact results |

跳过交互页：

Skip the interactive page:

```bash
lunar-gap-fit 2004-07-24 --no-interactive
```

---

## 辅助功能 · Helper Options

预测某一年拟合 gap：

Predict fitted gap for a target year:

```bash
lunar-gap-fit 2004-07-24 --predict-year 2042
```

查找输入年份之后的下一次精确重合：

Find the next exact coincidence after the input year:

```bash
lunar-gap-fit 2004-07-24 --find-next-coincidence
```

从指定年份之后开始搜索：

Search after a specific year:

```bash
lunar-gap-fit 2004-07-24 --find-next-coincidence --after-year 2026
```

生日模式：

Birthday shortcut:

```bash
lunar-gap-fit 2004-07-24 --birthday-mode
```

常用辅助参数 / Common helper flags:

```text
--predict-year YEAR
--find-next-coincidence
--after-year YEAR
--birthday-mode
--pretty
```

---

## 周期选择 · Period Selection

默认情况下，模型不会强行假设固定周期，而是自动扫描候选周期和谐波数。

By default, the model scans candidate periods and harmonic counts instead of assuming one fixed period.

```bash
--period auto
--harmonics auto
```

默认候选周期 / Default candidate periods:

```text
8, 11, 19, 38, 57, 76, 95, 114, 133, 152, 171, 190
```

固定周期和谐波数：

Use a fixed period and harmonic count:

```bash
lunar-gap-fit 2004-07-24 --period 95 --harmonics 40
```

---

## 输出文件 · Outputs

```text
gap_series.csv       # 逐年 gap 数据 / year-by-year gap data
coefficients.json    # 模型、系数和误差指标 / model, coefficients, and error metrics
formula.py           # 独立 Python 拟合函数 / standalone fitted function
interactive.html     # 离线交互函数图 / offline interactive graph
fit.png              # 静态图，除非使用 --no-plot / static plot unless --no-plot is used
report.md            # Markdown 报告 / Markdown report
```

---

## Gap 定义 · Gap Definition

```text
gap(Y) = matched lunar-anchor date - date(Y, solar_month, solar_day)
```

| 值 | 中文 | English |
| --- | --- | --- |
| 正数 | 农历匹配日期更晚 | lunar date is later |
| 负数 | 农历匹配日期更早 | lunar date is earlier |
| 0 | 精确重合 | exact coincidence |

---

## 日历准确性 · Calendar Accuracy

本项目使用内置编码农历表，并以香港天文台 Gregorian-Lunar Calendar Conversion Table 1901-2100 作为数据口径。测试会校验表编码 hash 和若干代表日期，避免日历表被误改后仍然“自洽但不准确”。

The project uses an encoded built-in lunar table aligned with the Hong Kong Observatory Gregorian-Lunar Calendar Conversion Table for 1901-2100. Tests check the table hash and representative dates so accidental table edits are visible.

交互页支持公历日期范围：`1901-01-01` 到 `2100-12-31`。

Interactive output supports Gregorian dates from `1901-01-01` through `2100-12-31`.

Source: https://www.hko.gov.hk/en/gts/time/conversion.htm

---

## 开发 · Development

运行测试 / Run tests:

```bash
python tests/test_basic.py
```

手动 smoke 命令 / Manual smoke commands:

```bash
python -m lunar_gap_fit 2004-07-24 --no-plot
python -m lunar_gap_fit 2004-07-24 --no-plot --no-interactive
python -m lunar_gap_fit 2005.2.4 --no-plot
python -m lunar_gap_fit 2005/2/4 --no-plot
python -m lunar_gap_fit 2004-07-24 --predict-year 2042 --no-plot
python -m lunar_gap_fit 2004-07-24 --find-next-coincidence --after-year 2026 --no-plot
python -m lunar_gap_fit 2004-07-24 --birthday-mode --no-plot
python -m lunar_gap_fit 2004-07-24 --birthday-mode --predict-year 2042 --pretty --no-plot
```

---

## 说明 · Notes

这是建模和拟合工具，不是官方历书。

This is a modeling and fitting tool, not an official almanac.
