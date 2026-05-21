---
name: translate_ipynb
description: 把已有的 .ipynb 笔记本里所有英文 markdown 内容翻译成中文,套用 /nb skill 的「暗色 + 色块语义 + 中文教学」视觉风格;代码 cell 完全不动。当用户说「翻译这个/这些 ipynb」「把英文 notebook 转成中文」「按 nb 风格本地化这几个笔记」时调用此 skill。可同时处理多个文件;若用户只给主题没给路径,先追问文件路径。
---

# `/translate_ipynb` — 把已有 ipynb 翻译成中文 + 套用 nb 样式

> 本 skill 修改 **用户指定的现有 .ipynb 文件**,把所有英文 markdown 内容翻译成中文,并按 `/nb` skill 的视觉规范包装。**代码 cell 一字不改**。**不创建新文件**,直接 in-place 修改原文件。

---

## 🔄 工作流程(每个 ipynb 走一遍)

1. **解析输入**:用户指定的 .ipynb 文件列表(可多个,通常一次处理一个)
2. **缺信息追问**:
   - 文件路径(用户给主题没给路径就问)
   - 是否真的 in-place 修改(默认是,如担心可先备份)
   - 风格强度:是否给每个段落都加 dark-* 色块(**默认:选择性应用**,详见下方「样式选择」)
3. **提取原文**:用 Bash + Python 把每个 markdown cell 的源文本打印出来(看清要翻译什么)
4. **逐 cell 设计翻译**:把原文映射成中文 + 合适的色块包装(见下方「翻译原则」「样式选择」)
5. **写一个 Python 脚本**:批量替换 markdown cell 的 `source`(代码 cell 跳过)
6. **校验 JSON 合法性**:`json.load()` 不报错
7. **回报**:简短列出每个文件改了多少 cell,不啰嗦总结

---

## 🎨 样式规范 —— **完全沿用 `/nb` skill**

色块定义、CSS 模板、调色板 hex 码 **不在这里重复**。请直接参考:
- `.claude/skills/nb/SKILL.md` 里的「冷调暗色调色板」「CSS 模板」「JSON 注意事项」

**简记 7 色语义**:

| 类名 | 用途 |
|------|------|
| `dark-title` | 渐变大标题(章节首) |
| `dark-info` | 概念引入、中性提示(蓝) |
| `dark-warning` | 关键洞察、易错点(黄) |
| `dark-error` | 反例、错误后果(红) |
| `dark-success` | 一句话带走、收尾(绿) |
| `dark-cyan` | 链接、LangSmith trace、官方资源(青) |
| `dark-orange` | 动手提示、新手 tip(橙) |

---

## 📋 翻译原则(**这是 skill 的核心**)

### ✅ 必须做

| 规则 | 说明 |
|------|------|
| **中文化解释性 prose** | 「This is important because...」→「这一点重要,因为...」 |
| **专业术语保留英文** | `MessagesState` / `bind_tools` / `Command(resume=...)` / `InMemoryStore` 等 API 名 **不译** |
| **保留图片 / 链接 / mermaid** | `![img](path)` 路径不变;`[link](url)` 链接 URL 不变,只翻 anchor text |
| **代码块内容不译** | ` ```python ... ``` ` 内的 Python 代码、注释里的 docstring(如属于函数说明)按情况处理 —— 普通注释可译,公开 API 的 docstring 保留英文 |
| **表格 > 段落** | 长段落能拆表的,优先拆成表 —— **可读性是首要目标** |
| **加 2026 视角的现代化补充** | 适度。在显眼的「**🆕 2026 提示**」`dark-cyan` 框里加,标明这是补充内容 |
| **保留学生视角** | 类比 / 对比 / 「为什么」 而不是「是什么」 |
| **每个 emoji 必有意义** | 🎯 = 目标 / 🔑 = 核心 / ⚠️ = 警告 / 💡 = 提示 / ✨ = 收尾 / 📎 = 链接 / 🆕 = 新内容 |

### ❌ 不要做

- ❌ **改动任何 code cell** —— `cell['cell_type'] == 'code'` 整个跳过
- ❌ **添油加醋翻译**(原文没的东西不要瞎编,但可以适度加 2026 视角的补充并标注)
- ❌ **把所有 cell 都包成色块**(过度样式化反而疲劳;见下方「样式选择」)
- ❌ **强译固定术语**(`ReAct` 不译成「反应模式」;`workflow` 不译成「工作流程」—— 行业里普遍说 workflow)
- ❌ **创建新文件** —— 直接 in-place 修改原 .ipynb
- ❌ **JSON 中文 unicode 转义**(`json.dump(..., ensure_ascii=False)` 必加)

---

## 🎨 样式选择(避免过度样式化的判断准则)

**核心准则**:**不是每个 markdown cell 都需要 dark-* 色块**。普通段落 / 简单列表保持干净 markdown,**只在以下情形** 加色块:

| 触发条件 | 用什么色块 |
|----------|-----------|
| H1/H2 章节首 + 一句话定位 | **dark-title** 渐变 |
| 这一段是「**这是关键概念,先解释**」 | **dark-info** 蓝 |
| 这一段是「**重点 / 易踩坑 / 反直觉**」 | **dark-warning** 黄 |
| 这一段在讲「**不这样做的后果**」 | **dark-error** 红 |
| 这一段是「**🆕 2026 视角补充**」 | **dark-cyan** 青(明确区分这是新增内容) |
| 这一段是「**💡 动手做一下**」 | **dark-orange** 橙 |
| **每章末尾** 的「**✨ 一句话带走**」 | **dark-success** 绿 |
| 普通解释、过渡段、列表 | **不加色块**,纯 markdown |

**判断口诀**:**问自己「读者扫眼时会想停在这一段吗?」**。会 → 加色块吸引注意;不会 → 让它低调融入。

---

## 🐍 Python 脚本模板(**实战可复用**)

为每个 .ipynb 写一个独立的 Python 脚本,放在 `/tmp/translate_<name>.py`,然后用 `python3` 跑。

```python
#!/usr/bin/env python3
"""Translate <FILENAME>.ipynb markdown cells to Chinese with /nb dark styling."""
import json
from pathlib import Path

NB_PATH = Path("/absolute/path/to/notebook.ipynb")

# 色块开/合标签(完全沿用 /nb skill 定义的 hex)
TITLE_OPEN = '<div class="dark-title" style="background:linear-gradient(90deg,#1e3a8a,#5b21b6); color:#f1f5f9; padding:20px 32px; border-radius:8px; width:97%;"><style>.dark-title strong{color:#fde047;}</style>\n\n'
INFO_OPEN  = '<div class="dark-info"  style="background:#1e293b; color:#e2e8f0; padding:12px 24px; border-left:4px solid #60a5fa; border-radius:4px; width:97%;"><style>.dark-info strong{color:#fbbf24;}</style>\n\n'
WARN_OPEN  = '<div class="dark-warning" style="background:#2a2418; color:#fde68a; padding:12px 24px; border-left:4px solid #fbbf24; border-radius:4px; width:97%;"><style>.dark-warning strong{color:#f9a8d4;}</style>\n\n'
SUCC_OPEN  = '<div class="dark-success" style="background:#1a2e1f; color:#bbf7d0; padding:10px 24px; border-left:4px solid #4ade80; border-radius:4px; width:97%;"><style>.dark-success strong{color:#fbbf24;}</style>\n\n'
CYAN_OPEN  = '<div class="dark-cyan"  style="background:#0f2729; color:#a5f3fc; padding:10px 24px; border-left:4px solid #22d3ee; border-radius:4px; width:97%;"><style>.dark-cyan strong{color:#fbbf24;}</style>\n\n'
ORNG_OPEN  = '<div class="dark-orange" style="background:#2d2418; color:#fed7aa; padding:10px 24px; border-left:4px solid #fb923c; border-radius:4px; width:97%;"><style>.dark-orange strong{color:#67e8f9;}</style>\n\n'
ERR_OPEN   = '<div class="dark-error" style="background:#2d1f1f; color:#fca5a5; padding:10px 24px; border-left:4px solid #f87171; border-radius:4px; width:97%;"><style>.dark-error strong{color:#fde047;}</style>\n\n'
CLOSE      = '\n\n</div>'

# 翻译表:index → 新 markdown 内容(完整字符串)
T = {}

T[0] = f"""{TITLE_OPEN}## 🎯 标题

**一句话定位**:这一节解决什么。{CLOSE}

{INFO_OPEN}**📚 学习要点**:...{CLOSE}"""

T[3] = f"""## 📋 普通章节标题

普通解释段落,不加色块。

| 表格 | 比段落更易扫 |
|------|--------------|
| ... | ... |"""

# ... 继续填其他 markdown cell 的 index

# === 执行替换 ===
with open(NB_PATH) as f:
    nb = json.load(f)

n = 0
for idx, src in T.items():
    if idx < len(nb['cells']) and nb['cells'][idx]['cell_type'] == 'markdown':
        nb['cells'][idx]['source'] = src.splitlines(keepends=True)
        n += 1
    else:
        print(f"⚠️  index {idx} 不是 markdown 或越界")

with open(NB_PATH, 'w') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)  # ⚠️ ensure_ascii=False 必加,否则中文变 \uXXXX

print(f'✅ 替换 {n} 个 markdown cell')

# 自校验
with open(NB_PATH) as f:
    json.load(f)
print('✅ JSON 仍合法')
```

### 📌 关键技术细节

| 注意 | 原因 |
|------|------|
| `ensure_ascii=False` | 不加的话中文全变成 `你好`,文件还能读但 diff 不清楚 |
| `indent=1` 或 `indent=2` | 保持 nbformat 习惯(`jupyter` 默认 1) |
| `src.splitlines(keepends=True)` | nbformat 要求 `source` 是字符串数组,每行末尾保留 `\n` |
| **不要** 用 `Edit` 一行行改 | markdown cell 经常有几十行;一次写整段 `source` 比 Edit 快得多 |
| **不要** 用 `NotebookEdit` | 它适合改单个 cell,批量翻译用直接 JSON 操作更快、更可控 |

---

## 📝 常用术语对照(默认这样译)

| 中文 | 英文 |
|------|------|
| 对话模型 | chat model |
| 工具调用 | tool calling / tool call |
| 工作流 | workflow(**不译**) |
| 反应式循环 | ReAct loop(**不译**) |
| 节点 | node |
| 边 / 条件边 | edge / conditional edge |
| 状态 | state(常保留英文)|
| 持久化 / 检查点 | persistence / checkpoint |
| 中断 / 续跑 | interrupt / resume |
| 人在回路 | human-in-the-loop / HITL(**通常保留英文**) |
| 子图 | subgraph |
| 派单 / 派发(给子 agent) | delegate to sub-agent |
| 信号型工具 | signal tool(本地术语,可用) |
| 副作用工具 | side-effect tool |
| 一句话带走 | take-away(中文表述) |
| 易踩坑 | pitfall / gotcha |

---

## 🚨 自查清单(脚本跑完前过一遍)

- [ ] 所有 code cell **完全没动** —— 脚本里 `if cell_type == 'markdown'` 做了过滤
- [ ] 所有色块都用 `width:97%;`(VSCode 右边缘截断)
- [ ] 所有色块都有 `class="dark-XXX"` + 内嵌 `<style>` 块
- [ ] 没有 **每个 cell 都包色块**(检查:夹杂着 `(纯 md)` 是好事)
- [ ] 至少 1 个 `dark-success` 绿框做章末「✨ 一句话带走」
- [ ] 图片 `![](path)` 路径 **没动**
- [ ] 链接 `[text](url)` 的 URL **没动**(只改 text)
- [ ] 关键 API / 类名保留英文(`MessagesState` 不变成「消息状态」)
- [ ] JSON 写完后 `json.load()` 不报错
- [ ] `ensure_ascii=False` 设了(中文不被转义)

---

## 💬 给用户的追问模板(若信息不全)

```
我要翻译哪几个文件?(给我绝对路径,或者说目录我列出来选)
是否直接 in-place 修改?(默认是,如想保留备份请说明)
要不要顺便加点 2026 视角的现代化补充?(默认:适度加,标在 dark-cyan 框里区分)
```

---

## 🔁 多文件场景

若用户一次给多个 .ipynb:

1. **用 TodoWrite 跟踪**(每个文件一个 todo)
2. **逐个处理**(一个文件一个 Python 脚本,放 `/tmp/translate_<n>.py`)
3. **每个完成后** 立刻更新 todo + 简短回报
4. **不要并发** —— 串行处理避免 token 浪费、便于失败回滚
5. **最后做一次合计** —— 用一个 Python 脚本扫所有文件,统计 cells / markdown 数 / 含中文数 / 含 dark-* 数

---

## 🎯 验证脚本模板(全部翻完后跑一遍)

```python
import json, re
files = ['0_a.ipynb', '1_b.ipynb', ...]  # 翻译过的文件
for f in files:
    with open(f) as fp: nb = json.load(fp)
    n_md = sum(1 for c in nb['cells'] if c['cell_type']=='markdown')
    n_zh = sum(1 for c in nb['cells'] if c['cell_type']=='markdown'
               and re.search(r'[一-鿿]', ''.join(c['source'])))
    n_styled = sum(1 for c in nb['cells'] if c['cell_type']=='markdown'
                   and 'dark-' in ''.join(c['source']))
    print(f'{f}: {n_md} md cells, {n_zh} 含中文, {n_styled} 带 dark-* 样式')
```

---

**End of skill.** 当用户调用 `/translate_ipynb <files>` 时,严格按此 skill 工作。代码 cell 神圣不可侵犯。
