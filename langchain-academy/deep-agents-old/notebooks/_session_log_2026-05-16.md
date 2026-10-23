# 🎓 Deep Agents 学习会话记录

**日期**:2026-05-16  
**主题**:LangChain Academy "Deep Agents from Scratch" 系统学习 + notebook 中文化美化  
**模型**:Claude Opus 4.7 (1M context)  
**工作目录**:`course-deep-agents-⏬👤/deep-agents-from-scratch/notebooks/`

---

## 🗺️ 会话总览

这次会话从"我看不懂 accessing state"开始,演变成一次完整的:
1. **概念深挖**:逐个搞懂 ReAct / InjectedState / Command / Recitation / Context Isolation 等核心概念
2. **trace 分析**:把多个 `agent.invoke()` 的 raw messages 输出逐条拆解
3. **notebook 大改造**:把 5 个英文教学 notebook 翻成中文 + 加视觉强化(emoji、渐变标题、彩色提示框)
4. **工程踩坑**:VSCode ipynb 右边文字被截 → padding → margin-right → 最终用 `width:97%` 解决
5. **精华提炼**:为每节课生成"本节精华回顾"`⭐️` 文件
6. **辅助产出**:可复用的 markdown 美化 prompt 模板

---

## 📁 本次会话产出的文件清单

### 主课文件(改造:英文 → 中文 + 视觉强化)
- `0_a_🔥_create_agent.ipynb`
- `1_a_🔥_todo.ipynb`
- `2_a_🔥_files.ipynb`
- `3_a_🔥_subagents.ipynb` (原名 `3_subagents.ipynb`,后被用户改名)
- `4_c_🔥_full_agent.ipynb` (原名 `4_full_agent.ipynb`,后被用户改名)

### 中间解释文件(`⭐️` 系列)
- `0_b_⭐️_tools_accessing_state.ipynb` — InjectedState 详解
- `0_c_⭐️_final_explanation.ipynb` — 13 条 messages 拆解
- `1_b_⭐️_read_todo()_&_write_todo().ipynb` — recitation 详解
- `1_c_⭐️_final_explanation.ipynb` — MCP query trace 分析
- `2_b_⭐️_description=_VS_docstring_for_tools.ipynb` — 工具 description 用法
- `2_c_⭐️_write_file_分页读取.ipynb` — offset/limit 设计(本应叫 read_file)
- `2_d_⭐️_messages_完整执行轨迹.ipynb` — MCP overview 8 条消息深度解读

### 精华回顾文件(本次会话末尾批量生成)
- `0_d_⭐️_本节精华.ipynb`
- `1_d_⭐️_本节精华.ipynb`
- `2_e_⭐️_本节精华.ipynb`
- `3_b_⭐️_本节精华.ipynb`
- `4_d_⭐️_本节精华.ipynb`

### 工具 / 模板文件
- `_PROMPT_notebook_beautify.md` — 可复用的中文 markdown 美化 prompt
- `_session_log_2026-05-16.md` — 本文件

---

## 🧭 关键概念地图(本次学到 / 巩固的)

### 1. ReAct Agent = 状态机

不是 LLM 自己在循环,而是 **LangGraph 这台有限状态机**在 `agent ↔ tools` 之间反复跳:

```
START → agent ──┬──► tools ──► agent   (无条件回边)
                └──► END                (条件边:AIMessage.tool_calls 为空就退出)
```

- `agent` 节点 = 调用 LLM → 产 `AIMessage`
- `tools` 节点 = `ToolNode` 并发执行所有 `tool_calls`
- 路由器看 `AIMessage.tool_calls` 是否为空决定下一步

**LLM 是无状态的** —— 每轮把完整 messages 重发,这是为什么 `input_tokens` 单调上涨。

### 2. State 注入(InjectedState / InjectedToolCallId)

工具想用 graph state,但 LLM 看不到 state,所以填不出 `state` 参数。

解法:`Annotated[CalcState, InjectedState]` → 框架把这两个参数从 LLM 看到的 schema 里**剥掉**,运行时由 `ToolNode` 自己注入。

```python
@tool
def calculator_wstate(
    operation, a, b,
    state: Annotated[CalcState, InjectedState],          # 不发给 LLM
    tool_call_id: Annotated[str, InjectedToolCallId],   # 不发给 LLM
):
    ...
```

### 3. Command 多字段更新

普通 return → 框架自动包成 ToolMessage。但要更新多个 state 字段,必须用 `Command`:

```python
return Command(update={
    "ops":      ops,
    "messages": [ToolMessage(f"{result}", tool_call_id=tool_call_id)],  # 必须自己造
})
```

**一旦用 Command,框架不再自动包 ToolMessage** → 必须自己造 → 必须有 `tool_call_id` → 必须 `InjectedToolCallId`。三者互为前提。

### 4. Recitation(背诵)模式 = 治 Context Rot

长任务里(20+ 工具调用),早期计划会被埋在 messages 最上方,LLM 注意力衰减、跑题。

解药:让 LLM 周期性调 `read_todos()` → **把 todos 塞回 messages 末尾** → 注意力被强制拉回任务。

`read_todos` 不是给程序员读的,是**给 LLM 自己读的"自我提示工具"**。

### 5. 文件 = 注意力开关

虚拟文件系统的真正作用不是"存数据",而是**控制 LLM 注意力**:
- 想让 LLM **暂时忘记**长内容 → `write_file` 把它移出 messages,只留文件名
- 想让 LLM **想起** → `read_file` 把它塞回 messages 末尾

经典套路:**Save → Search → Read-Back**。

### 6. file_reducer:并行场景的"救生圈"

```python
def file_reducer(left, right):
    return {**left, **right}    # right 同名 key 覆盖 left
```

**单线程顺序写不需要**(因为 `write_file` 自己已经"读旧+加新+返回完整 dict")。

**必需的场景**:
- LLM 一次发多个 `write_file` tool_call → ToolNode 并行执行 → 各读同一快照 → 默认 reducer 会丢
- 子 agent 提交 files 回父 agent → 父 files + 子 files 必须合并

### 7. Context Isolation = 开新 context

multi-agent 架构的核心。`task` 工具的灵魂一行:

```python
state["messages"] = [{"role": "user", "content": description}]   # 擦掉父历史
result = sub_agent.invoke(state)
```

把 messages 清空,只留任务描述。子 agent 在干净 context 跑,完全不受父对话历史污染。

避免 **4 类 context 病**:Clash(冲突)/ Confusion(混乱)/ Poisoning(污染)/ Dilution(稀释)。

### 8. 三大模块对应三类病

Deep Agent = ReAct 循环 + 3 件武器:

| 武器 | 治什么 |
|---|---|
| 📋 **TODOs** | 治"忘"(context rot)|
| 📁 **Files** | 治"挤"(context bloat)|
| 🚀 **Subagents** | 治"乱"(context clash/confusion)|

合起来 = 一台能跑 50+ 工具调用还不崩的研究 agent。

### 9. Tool 设计精髓(本课贡献的反直觉认知)

- 🎯 **`description=` 接管 LLM 视角**:写了它,docstring 对 LLM 就消失(除非 `parse_docstring=True` 暴露 `Args:`)
- 🎯 **错误信息的目标读者 = LLM,不是人**:要技术化、具体、信息密集(`Error: File 'foo.txt' not found`,不是"哎呀出错了 😅")
- 🎯 **`offset` + `limit` 分页**:让 LLM 自己决定读多少,对抗大文件爆 context(Claude Code 同款)
- 🎯 **工具留口子,LLM 来填创意**:`write_file(file_path, content)` 的 content 是无 schema 字符串,LLM 可以**给未来的自己写笔记**(这就是 `Topics to cover` 凭空出现的本质)
- 🎯 **`think_tool` 是"自我提示工具"**:什么都不做,只让思考留痕

---

## 📜 关键 Q&A 摘录(按时间顺序)

### Q1:在 0_a 这个笔记里 accessing state 我没看懂

**A**:核心难题是 LLM 看不到 state 但工具需要 state。解法是 `InjectedState` 注解 —— 把 state 参数从发给 LLM 的 schema 里剥掉,运行时由框架自动注入。
配套 `Command` 用于同时更新多个 state 字段,但需要手动造 ToolMessage,所以也需要 `InjectedToolCallId`。三者互为前提。

### Q2:`((15+23)x64+52)/6` 是怎么运行的?

**A**:4 轮 LLM 调用,7 次工具调用。
- 第 1 轮:LLM 一次发出 4 个并行 tool_call(add 15+23、乘 64×1、加 52+0、除 6÷1)—— 其中 3 个是 no-op,LLM 想并行但只能对叶子常量并行
- 第 2-4 轮:串行算 38×64=2432 → 2432+52=2484 → 2484/6=414
- 最后:LLM 给出 "The result is 414.0",`tool_calls=[]`,退出循环
- input_tokens 单调上涨:192 → 328 → 363 → 399 → 436

### Q3:消息 5(4 个 ToolMessage)是怎么跳到消息 6(下一个 AIMessage)的?

**A**:走 `tools → agent` 这条**无条件回边**。`tools` 节点跑完后,框架不需要决策,直接调 `agent` 节点,把更新后的整个 `messages` 重新喂给 LLM。条件边只在 `agent` 节点之后存在(看 tool_calls 是否为空)。

### Q4:`read_todos()` 这个方法的意图是什么?我看不懂

**A**:它不是给程序员读的,是**给 LLM 自己读的**。
- `state["todos"]` 是权威存储(LLM 不可见)
- `state["messages"]` 是 LLM 唯一视线
- `read_todos` 把 todos 从权威存储读出,**塞回 messages 末尾** → 把 LLM 注意力从无关搜索结果拉回任务计划
- 这是 Manus 风格的 "recitation"(背诵)模式,治 context rot

### Q5:`Topics to cover` 这些项是怎么凭空被加进 mcp_request.txt 里的?

**A**(改进版,最易懂):
- **核心认知**:LLM 只做"文本生成"一件事。它产生的所有东西,无论看起来是自然语言还是 tool call,**本质都是 token 一个一个吐出来**
- `content="..."` 这个字符串 = LLM 当场打字打出来的,跟它写"## Overview of MCP"完全同一回事
- 工具(`write_file`)是**纯被动管道**,原样落盘,不做任何加工
- LangChain 也没"加任何东西",纯搬运
- 类比:让朋友帮你记笔记,机械型只写"买牛奶",聪明型会加 TODO + 联想 —— **LLM 就是聪明型朋友**
- 验证:换个用户请求(比如"番茄面食谱"),topics 会完全不同 → 证明是即兴生成,不是模板

### Q6:`file_reducer` 用默认 reducer 行不行?

**A**(经过反复澄清):
- **单线程顺序写**:有没有 file_reducer **结果都一样**,因为 `write_file` 自己已经"读旧+加新+返回完整 dict",所以 update 本身就是完整版,默认覆盖 vs 合并结果一致
- **必需 file_reducer 的场景**:
  - 并行写(同一 AIMessage 多 tool_call):各 call 读到同一快照,默认 reducer 会丢
  - 子 agent 提交回父:父 files + 子 files 必须合并

### Q7:VSCode ipynb 里右边文字被挡住怎么办?

**A**(踩坑过程):
1. ❌ `padding` 加右边距 → 不行(padding 只能让文字离 div 边远,div 本身仍贴 cell 边)
2. ❌ `margin-right: 24px` → 不行(VSCode 渲染器可能强制 width:100% 把 margin 吸收)
3. ✅ **`width: 97%`** → 终极解 —— 直接限制 div 宽度到 97%,剩下 3% 自然成右边距,渲染器无法绕过

### Q8:为什么 ipynb 里 Cmd+Click 跳源码经常失败?

**A**:Jupyter notebook + VSCode 的公认痛点。原因:Pylance(LSP)和 Jupyter 扩展协作不稳定,interpreter 和 kernel 可能不一致,Pylance 默认不索引外部包。
排查顺序:Select Interpreter → 重启 Pylance → 开 `useLibraryCodeForTypes` → 确认 langgraph 装在当前环境 → 用 `.py` 文件验证。
应急方案:`python -c "from langgraph.types import Command; import inspect; print(inspect.getsourcefile(Command))"` 手动定位。

---

## 🎨 视觉设计系统(本次会话建立的规范)

详见 `_PROMPT_notebook_beautify.md`。核心要点:

### CSS 模板(所有 div 必须带 `width:97%`!)

```html
<!-- 章节标题(渐变) -->
<div style="background:linear-gradient(90deg,#0366d6,#6f42c1); color:white; padding:20px 32px; border-radius:8px; width:97%;">

## 🎯 标题文字

</div>

<!-- 提示框 -->
<div style="background:#fff3b0; padding:12px 24px; border-left:4px solid #f0ad4e; border-radius:4px; width:97%;">
警告内容
</div>
```

### 配色系统

| 颜色 | 用途 |
|---|---|
| 蓝 `#0366d6` / `#e8f4fd` | 信息 / 概念 |
| 黄 `#f0ad4e` / `#fff3b0` | 警告 / Note |
| 红 `#d9534f` / `#ffe6e6` | 错误 / 危险 |
| 绿 `#28a745` / `#e7f7e9` | 成功 / 重点 / 一句话总结 |
| 青绿 `#1abc9c` / `#f0f9ff` | LangSmith / 引用 |
| 橙 `#ff9800` / `#fff8e1` | 动手提示 / 警示 |

### 内容规则

- 🌐 翻译成中文,**专有名词保留英文**(AIMessage / ToolNode / InjectedState 等)
- ✂️ 言简意赅,不要扩写超过原文 1.5 倍
- 📊 长段落 → 表格 / 带 emoji 列表
- 💡 末尾加"一句话总结"用 block quote
- 🎯 每个 emoji 都要有信息含义,不做装饰

---

## 🧱 核心架构图(全课心智模型)

```
                ┌───────────────────────────────────────┐
                │   👨‍✈️ Supervisor (主 agent)              │
                │   ──────────────────────────────────   │
                │   工具:                               │
                │   • write_todos / read_todos   📋     │  ← TODO(治忘)
                │   • ls / read_file / write_file 📁    │  ← Files(治挤)
                │   • task                       🚀    │  ← Subagent(治乱)
                │   • think_tool                 🧘    │
                └────────────────┬──────────────────────┘
                                 │ task(description, subagent_type)
                                 ▼
                ┌───────────────────────────────────────┐
                │   🧑‍🔬 Research Sub-agent                │
                │   (开新 context,看不到父历史)        │
                │   工具:                               │
                │   • tavily_search    🔍 (落盘+摘要)   │
                │   • think_tool       🧘               │
                └───────────────────────────────────────┘
```

---

## 🌍 与真实产品的对应

| 本课概念 | 现实里的实现 |
|---|---|
| ReAct 循环 | Claude Code / Cursor Agent / Devin 核心驱动 |
| TODO recitation | Claude Code 的 `TodoWrite` 工具 |
| Context offloading 文件系统 | Manus / HF Open Deep Research / Anthropic Multi-Agent |
| `offset + limit` 分页读 | Claude Code 的 `Read` 工具同款 |
| `task` 派单 + Sub-agents | Claude Code 的 general-purpose agent + Task tool |
| `tavily_search` 落盘+摘要 | Perplexity Pro Search / Claude Search |
| `deepagents` 包 | LangChain 1.0 官方推荐的 deep agent 起点 |

---

## 🛠️ 工具命令速查

### uv 环境管理
```bash
uv sync                  # 装依赖
uv run jupyter notebook  # 跑 notebook
source .venv/bin/activate; jupyter notebook  # 老办法
```

### LangGraph Studio
```bash
langgraph up
```

### 调试 Cmd+Click 不工作
```bash
which python
python -c "import langgraph; print(langgraph.__file__)"
python -c "from langgraph.types import Command; import inspect; print(inspect.getsourcefile(Command))"
```

VSCode `settings.json` 加:
```json
{
  "python.analysis.useLibraryCodeForTypes": true,
  "python.analysis.indexing": true,
  "python.languageServer": "Pylance"
}
```

---

## 💎 5 年后重读时,最该记住的 8 句话

1. **Agent ≠ LLM。Agent = LangGraph 跑的状态机**,LLM 只是状态机里其中一个节点。
2. **LLM 是无状态的**,每轮把完整 messages 重发 → input_tokens 单调上涨。
3. **Tool call 的所有参数都是 LLM 当场打字打出来的**,不是代码提取,不是模板填充。
4. **`read_todos` / `read_file` / `think_tool` 都是"自我提示工具"** —— 给未来的自己写笔记,不获取新信息。
5. **文件 ≠ 数据库,文件 = LLM 的注意力开关**。Save → Search → Read-Back 是经典套路。
6. **Context Isolation 的灵魂只有一行**:`state["messages"] = [{"role": "user", "content": description}]`。
7. **Deep Agent = ReAct 循环 + 3 件武器**:TODO 治忘、Files 治挤、Subagents 治乱。
8. **VSCode ipynb 里所有自定义 div 都必须带 `width:97%`**,否则右边会被滚动条 / cell action 按钮挡住。

---

## 🎓 学习路径建议(5 年后想复习时)

按这个顺序读:

1. **`0_d_⭐️_本节精华.ipynb`** — 复习 ReAct 循环 + State 注入(最重要的地基)
2. **`1_d_⭐️_本节精华.ipynb`** — 复习 Recitation 模式
3. **`2_e_⭐️_本节精华.ipynb`** — 复习虚拟文件系统(注意力开关)
4. **`3_b_⭐️_本节精华.ipynb`** — 复习 Context Isolation
5. **`4_d_⭐️_本节精华.ipynb`** — 看三者如何组合(收官)

如果某节卡住,回到对应的 `_a_🔥_*.ipynb` 主课文件看完整中文版。

需要"啊原来这样"的瞬间?去翻对应的 `_b_/_c_/_d_/_e_⭐️_*.ipynb` 解释文件,那里有最详细的 trace 拆解 + 类比 + 反直觉认知。

---

## 📌 待办 / 可能的后续问题

(你 5 年后再回来时,可能想做的:)

- [ ] **跑通主课所有 cell**(本次会话主要是改 markdown,代码 cell 没全跑过)
- [ ] **用 `deepagents` 包实战一个自己的项目**(参考 4_d 末尾)
- [ ] **学 LangSmith 用法**(trace、eval、prompt 工程)—— 本课提到但没细讲
- [ ] **比对 Anthropic Multi-Agent Research 论文**(本课很多设计来自那)
- [ ] **看 LangGraph 1.0 文档的 hooks 章节**(0_a 提到但本课没细讲)

---

## 🔧 元信息

- **会话累计输入 tokens**:数十万级别(具体看 LangSmith 或 API console)
- **生成文件数**:18 个(5 个主课改造 + 7 个详细解释 + 5 个精华回顾 + 1 个 prompt 模板 + 本日志)
- **核心心智模型数**:9 个(见上方"关键概念地图")
- **CSS 调试轮次**:3 次(padding → margin-right → **width:97% ✅**)
- **同一概念被反复澄清的次数**:`file_reducer` 必要性被问了 3 次,LLM 生成 tool call 参数被问了 2 次 —— 这俩是最反直觉的点,5 年后如果忘了也很正常,直接来 Q5 + Q6 复习

---

## ✨ 这次会话最值得带走的"金句"

> 1. **"循环不在 LLM 里,在 LangGraph 这台状态机里"**
> 2. **"工具留口子,LLM 来填创意"**(关于 write_file 的 content 是开放字符串)
> 3. **"文件 = LLM 的注意力开关"**(不是存储,是注意力管理)
> 4. **"`read_todos` 不是给程序员读的,是给 LLM 自己读的"**
> 5. **"Deep Agent = ReAct 循环 + 3 件武器治 3 类病"**
> 6. **"写诗和写参数,对 LLM 来说是同一件事"**(关于 tool_call 本质)

---

**End of session log.** Save this file carefully — 5 年后回来,这是回忆这场对话的最快入口。

— Generated by Claude Opus 4.7, 2026-05-16
