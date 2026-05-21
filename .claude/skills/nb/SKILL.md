---
name: nb
description: 生成一个全新的 Jupyter notebook (.ipynb),遵循本仓库已建立的「中文教学 + 冷调暗色 + 色块标注」视觉风格。当用户说「写一个笔记」「新建 ipynb」「生成一个讲解 X 的 notebook」「用之前那种风格做一个笔记」时调用此 skill。用户可同时提供主题、内容要点、目标路径;若信息不全,先追问。
---

# `/nb` — 中文暗色教学 notebook 生成器

> 本 skill 输出一份 `.ipynb` 文件,严格遵循本仓库的「**冷调暗色 + 色块语义 + 中文教学**」既定风格。
> 用户主要在 deep-agents-from-scratch 课程下使用,但本 skill 适用于本仓库任何课程子目录。

---

## 🔄 工作流程(调用时按顺序做)

1. **解析用户输入**(slash command 后跟的参数 = 主题描述)
2. **缺信息就问**:
   - 文件保存位置(默认:当前打开的 ipynb 同目录,或者用户最近 cd 的 `notebooks/`)
   - 文件名(参考下文「命名规范」)
   - 目标长度 / 详细程度(快速 200 字版 / 标准 500 字版 / 深度 1000+ 字版)
3. **生成 .ipynb**:用 `Write` 工具直接产出 JSON。每个 markdown 单元格按下方「**结构模板**」组装。
4. **校验**:
   - 所有 `<div>` 必须含 `width:97%;`(VSCode 右边缘截断 bug)
   - 所有色块必须有 `class="dark-XXX"` + 内嵌 `<style>` 块定义 `.dark-XXX strong{color:...}`
   - JSON 合法(`<div>` 内的 markdown 内容前后留空行,否则不解析)
5. **回报**:简短列出结构、单元格数、文件路径,不啰嗦总结。

---

## 🎨 冷调暗色调色板(**绝不更改的硬规则**)

### 7 种色块语义

| 类名 | 语义 / 用途 | 背景 | 正文色 | 边框 | 粗体色 |
|---|---|---|---|---|---|
| `dark-title` | 渐变标题(章节大字) | `linear-gradient(90deg,#1e3a8a,#5b21b6)` | `#f1f5f9` | — | `#fde047` 亮黄 |
| `dark-info` | 信息 / 中性提示 / 蓝色 | `#1e293b` | `#e2e8f0` | `#60a5fa` | `#fbbf24` 琥珀 |
| `dark-warning` | 警告 / 关键洞察 / 黄色 | `#2a2418` | `#fde68a` | `#fbbf24` | `#f9a8d4` 粉红 |
| `dark-error` | 错误 / 反例 / 红色 | `#2d1f1f` | `#fca5a5` | `#f87171` | `#fde047` 亮黄 |
| `dark-success` | 成功 / ✨ 一句话带走 / 绿色 | `#1a2e1f` | `#bbf7d0` | `#4ade80` | `#fbbf24` 琥珀 |
| `dark-cyan` | LangSmith / 链接 / 青色 | `#0f2729` | `#a5f3fc` | `#22d3ee` | `#fbbf24` 琥珀 |
| `dark-orange` | 动手提示 / 警示弱化 / 橙色 | `#2d2418` | `#fed7aa` | `#fb923c` | `#67e8f9` 浅青 |

**粗体色挑选原则**:对正文色做**异色相**对比(冷暖跨色),不要同色相亮度差。

### 代码块 `<pre>`

```
background:#1e1e2e; color:#d4d4d4; padding:10px 24px; border-radius:4px; font-size:0.90em; width:97%;
```

### 行内高亮 `<span>`

```
background:#3d3414; color:#fde047; padding:0 2px;
```

---

## 📐 CSS 模板(**直接复制粘贴用**)

### 渐变标题(大节、章节首)

```html
<div class="dark-title" style="background:linear-gradient(90deg,#1e3a8a,#5b21b6); color:#f1f5f9; padding:20px 32px; border-radius:8px; width:97%;"><style>.dark-title strong{color:#fde047;}</style>

## 🎯 章节标题

**一句话定位**:这一节解决什么问题。

</div>
```

### 信息蓝框

```html
<div class="dark-info" style="background:#1e293b; color:#e2e8f0; padding:12px 24px; border-left:4px solid #60a5fa; border-radius:4px; width:97%;"><style>.dark-info strong{color:#fbbf24;}</style>

正文 + **关键词**

</div>
```

### 警告黄框(关键洞察)

```html
<div class="dark-warning" style="background:#2a2418; color:#fde68a; padding:12px 24px; border-left:4px solid #fbbf24; border-radius:4px; width:97%;"><style>.dark-warning strong{color:#f9a8d4;}</style>

**关键洞察**:这是个易错点 / 反直觉的地方。

</div>
```

### 错误红框(反例)

```html
<div class="dark-error" style="background:#2d1f1f; color:#fca5a5; padding:10px 24px; border-left:4px solid #f87171; border-radius:4px; width:97%;"><style>.dark-error strong{color:#fde047;}</style>

**后果**:如果不这样做,会出现什么问题。

</div>
```

### 成功绿框(✨ 一句话带走)

```html
<div class="dark-success" style="background:#1a2e1f; color:#bbf7d0; padding:10px 24px; border-left:4px solid #4ade80; border-radius:4px; width:97%;"><style>.dark-success strong{color:#fbbf24;}</style>

**一句话**:本节的核心 take-away。

</div>
```

### 青色框(链接、LangSmith)

```html
<div class="dark-cyan" style="background:#0f2729; color:#a5f3fc; padding:10px 24px; border-left:4px solid #22d3ee; border-radius:4px; width:97%;"><style>.dark-cyan strong{color:#fbbf24;}</style>

延伸:**LangSmith trace**、官方文档、外链。

</div>
```

### 橙色框(动手提示)

```html
<div class="dark-orange" style="background:#2d2418; color:#fed7aa; padding:10px 24px; border-left:4px solid #fb923c; border-radius:4px; width:97%;"><style>.dark-orange strong{color:#67e8f9;}</style>

💡 **动手试试**:运行下面这段代码看看输出。

</div>
```

### 代码块(可高亮某一行)

```html
<pre style="background:#1e1e2e; color:#d4d4d4; padding:10px 24px; border-radius:4px; font-size:0.90em; width:97%;">
<code class="language-python">
some_code(<span style="background:#3d3414; color:#fde047; padding:0 2px;">highlighted_part</span>)
</code></pre>
```

---

## 🏗️ 标准结构模板(笔记的骨架)

```
1. 渐变标题(dark-title) + 一句话定位
2. 信息蓝框(dark-info):问题来源 / 上下文
3. 渐变小标题(dark-title H3):「第一步:字面拆解」
4. 表格 + 解释段落
5. 渐变小标题:「第二步:擦掉 vs 保留」/ 「核心机制」
6. 警告黄框(dark-warning):关键洞察
7. 渐变小标题:「类比」
8. 表格(正反对比 / 像 vs 不像)
9. 渐变小标题:「反例 / 不这样做会怎样」
10. 代码块(<pre>)+ 错误红框(dark-error)
11. 渐变小标题:「✨ 一句话带走」
12. 成功绿框(dark-success):金句收尾
```

**最小骨架**(适合短笔记):标题 → 内容 → 绿框收尾。

---

## ✍️ 风格 / 语气铁律

### 必须做

- **中文输出**(除非用户明确要求英文)
- **每个 emoji 必有意义**(🔑 = 核心 / 🎯 = 目标 / ✨ = 收尾 / ⚠️ = 警告 / 💡 = 提示 / 🔬 = 反例)
- **表格 > 段落**,**列表 > 句子**,**代码 > 描述**
- 专有名词保留英文(`AIMessage`、`ToolNode`、`InjectedState`、`Command`)
- 每节末尾用 `dark-success` 绿框做「一句话带走」收尾
- 所有 `<div>`/`<pre>` 必须 `width:97%;`(否则 VSCode 右边缘截断)

### 不要做

- ❌ 写「接下来我们将…」「让我们开始吧」之类的填充语
- ❌ 装饰性 emoji(每个都要承担信息)
- ❌ 把英文专有名词强译(`ReAct` 不译成「反应模式」)
- ❌ 给 `<div>` 加 `margin-right`(VSCode 忽略;只有 `width:97%` 起作用)
- ❌ 多段同色块连用(信息蓝 → 信息蓝 →…读者会麻木)

---

## 📝 既定术语对照(用这些词,不要发明新词)

| 中文 | 英文 |
|---|---|
| ReAct 循环 / 状态机 | ReAct loop |
| 工具节点 | ToolNode |
| 注入 | InjectedState / InjectedToolCallId |
| 派单 / 派发 | delegate(to sub-agent) |
| 复述 | recitation(Manus 术语) |
| 注意力开关 | attention switch |
| 自我提示工具 | self-prompt tool |
| context rot | context rot(不译) |
| 隔离 context | isolated context |
| 落盘 | persist to file |
| 治忘 / 治挤 / 治乱 | TODO 治忘 / Files 治挤 / Subagents 治乱 |

---

## 📂 文件命名规范

| 模式 | 含义 |
|---|---|
| `N_a_🔥_*.ipynb` | 主课(来自 LangChain Academy 原始翻译) |
| `N_X_⭐️_*.ipynb` | 补充讲解(X = b, c, d, ...) |
| `N_z_⭐️_本节精华.ipynb` | 每课最末的精华总结 |
| `_*.md` / `_*.py` | 元文件 / 脚本(下划线前缀) |

**生成新补充笔记时**:用 `ls notebooks/` 看一下当前课次最大字母,挑下一个(b→c→d→e...)。

---

## 🧱 完整 .ipynb JSON 框架(填空即可)

```json
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "<div class=\"dark-title\" style=\"background:linear-gradient(90deg,#1e3a8a,#5b21b6); color:#f1f5f9; padding:20px 32px; border-radius:8px; width:97%;\"><style>.dark-title strong{color:#fde047;}</style>\n",
    "\n",
    "## 🎯 [标题]\n",
    "\n",
    "**一句话定位**:[内容]\n",
    "\n",
    "</div>"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {"display_name": ".venv", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.11"}
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
```

**JSON 注意事项**:
- 每个 cell 的 `source` 是字符串数组,每个元素以 `\n` 结尾(最后一个除外)
- HTML 里的双引号在 JSON 里要 `\"`
- 中文直接写,**不要** `\u` 转义(`Write` 工具默认 UTF-8)

---

## 🚨 调用时必查清单(self-check before Write)

- [ ] 每个 `<div>` 含 `class="dark-XXX"` + 内嵌 `<style>` 块
- [ ] 每个 `<div>`/`<pre>` 含 `width:97%;`
- [ ] 渐变只用 `linear-gradient(90deg,#1e3a8a,#5b21b6)` 或其他既定渐变,**不用浅色**
- [ ] 至少 1 个 `dark-success` 绿框收尾
- [ ] 每个 emoji 都承担信息(不是装饰)
- [ ] 文件名遵循 `N_X_⭐️_主题.ipynb` 命名
- [ ] JSON 用 `Write` 保存为 UTF-8,中文不转义

---

## 💬 给用户的追问模板(若信息不全)

```
我要在哪个目录创建?(默认: course-deep-agents-⏬👤/deep-agents-from-scratch/notebooks/)
文件名想叫什么?(我可以按 N_X_⭐️_主题 自动起名,你提供「N」和「主题」即可)
篇幅:短(~3 cells)/ 标准(~6-8 cells)/ 长(10+ cells)?
```

---

**End of skill. 当用户调用 `/nb <内容>` 时,严格按此 skill 输出。**
