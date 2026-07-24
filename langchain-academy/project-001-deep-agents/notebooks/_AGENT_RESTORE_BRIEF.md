# Agent Session Restoration Brief

> **Audience**: Future Claude Code (or any LLM agent) resuming this user's session.
> **Date written**: 2026-05-16  
> **Read this first**, then proceed with the user's request.

---

## 🎯 TL;DR (read this if nothing else)

User is **学习 LangChain Academy "Deep Agents from Scratch" 中文学习者**, working through 5 教学 notebooks. They've established a **detailed visual + naming convention** for notebooks. **Follow the convention exactly** — they've spent many turns debugging and refining it.

**Critical rule**: Every custom `<div>`/`<pre>` block in `.ipynb` files MUST include `width:97%;` in style, otherwise VSCode's ipynb renderer cuts off right-edge text.

---

## 👤 User Profile

| Attribute | Value |
|---|---|
| **Primary language** | 中文(Simplified Chinese)|
| **Tool experience** | Familiar with Python, LangChain, Jupyter; learning agents from scratch |
| **Editor** | VSCode (ipynb notebooks rendered natively, has known Cmd+Click limitations) |
| **Package manager** | `uv` (preferred), env at `.venv/` |
| **API access** | Anthropic (Claude), OpenAI, LangSmith, Tavily — all set up via `.env` |
| **Asks pointed questions** | When confused, asks for "更易懂的方式" — prefers analogies + verification + counterexamples |
| **Will reject vague answers** | Pushes back: "我看不懂", "依旧不行" — demands clarity over politeness |
| **Likes** | Tables, emoji-anchored bullets, gradient headers, colored boxes, before/after comparisons, "一句话总结" 收尾 |
| **Dislikes** | Wordy filler ("接下来我们将…"), repetition, decorative emoji (each emoji must mean something), generic platitudes |

---

## 📂 Project Layout

**Working directory**:  
`/Users/bohaoli/Desktop/tuto/tuto_langchain/official/langchain-langgraph-langsmith/course-deep-agents-⏬👤/deep-agents-from-scratch/`

**Active subdirectory**: `notebooks/`

**Course source**: LangChain Academy — "Deep Agents from Scratch" (5-lesson sequence)

**Path quirks**:
- Parent dir has emoji in name (`⏬👤`) — needs proper Unicode handling in shells
- Notebook filenames contain `🔥` and `⭐️` (intentional, user's convention)

---

## 📁 File Inventory (Don't Re-Create These)

### Main lesson files (改造过:英文→中文+视觉强化)
| File | Topic |
|---|---|
| `0_a_🔥_create_agent.ipynb` | ReAct agent, InjectedState, Command |
| `1_a_🔥_todo.ipynb` | TODO list, recitation pattern |
| `2_a_🔥_files.ipynb` | Virtual filesystem, context offloading |
| `3_a_🔥_subagents.ipynb` | Context isolation, sub-agents |
| `4_c_🔥_full_agent.ipynb` | Full deep agent, Tavily search |

### Explanation files (`⭐️` series — supplementary deep-dives)
| File | Purpose |
|---|---|
| `0_b_⭐️_tools_accessing_state.ipynb` | InjectedState/Command deep-dive |
| `0_c_⭐️_final_explanation.ipynb` | 13-message trace breakdown |
| `1_b_⭐️_read_todo()_&_write_todo().ipynb` | Recitation pattern |
| `1_c_⭐️_final_explanation.ipynb` | MCP query trace |
| `2_b_⭐️_description=_VS_docstring_for_tools.ipynb` | Tool description vs docstring |
| `2_c_⭐️_write_file_分页读取.ipynb` | offset/limit pagination (misnamed — actually about read_file) |
| `2_d_⭐️_messages_完整执行轨迹.ipynb` | MCP overview 8-message walkthrough |

### Summary files (本次会话末尾生成,统一格式)
| File | Topic |
|---|---|
| `0_d_⭐️_本节精华.ipynb` | Lesson 0 essentials |
| `1_d_⭐️_本节精华.ipynb` | Lesson 1 essentials |
| `2_e_⭐️_本节精华.ipynb` | Lesson 2 essentials |
| `3_b_⭐️_本节精华.ipynb` | Lesson 3 essentials |
| `4_d_⭐️_本节精华.ipynb` | Lesson 4 essentials |

### Meta files
| File | Purpose |
|---|---|
| `_PROMPT_notebook_beautify.md` | **Reusable prompt template** — paste to any LLM for the same beautification style |
| `_session_log_2026-05-16.md` | Human-readable session journal |
| `_AGENT_RESTORE_BRIEF.md` | **This file** (agent restoration) |

### Source code (do NOT modify unless asked)
`../src/deep_agents_from_scratch/`:
- `state.py` — DeepAgentState, file_reducer
- `file_tools.py` — ls, read_file, write_file
- `todo_tools.py` — write_todos, read_todos
- `task_tool.py` — _create_task_tool, SubAgent
- `research_tools.py` — tavily_search, think_tool
- `prompts.py` — all instruction templates

---

## 🎨 Established Visual Convention (FOLLOW EXACTLY)

### Critical CSS pattern

```html
<!-- Section header (gradient) -->
<div style="background:linear-gradient(90deg,#0366d6,#6f42c1); color:white; padding:20px 32px; border-radius:8px; width:97%;">

## 🎯 Title

</div>

<!-- Info box (blue) -->
<div style="background:#e8f4fd; padding:12px 24px; border-left:4px solid #0366d6; border-radius:4px; width:97%;">
content
</div>

<!-- Warning (yellow) -->
<div style="background:#fff3b0; padding:12px 24px; border-left:4px solid #f0ad4e; border-radius:4px; width:97%;">

<!-- Error (red) -->
<div style="background:#ffe6e6; padding:10px 24px; border-left:4px solid #d9534f; border-radius:4px; width:97%;">

<!-- Success / Key takeaway (green) -->
<div style="background:#e7f7e9; padding:10px 24px; border-left:4px solid #28a745; border-radius:4px; width:97%;">

<!-- LangSmith / link (cyan) -->
<div style="background:#f0f9ff; padding:10px 24px; border-left:4px solid #1abc9c; border-radius:4px; width:97%;">

<!-- Hands-on hint (orange) -->
<div style="background:#fff8e1; padding:10px 24px; border-left:4px solid #ff9800; border-radius:4px; width:97%;">

<!-- Highlighted code block -->
<pre style="background:#f6f8fa; padding:10px 24px; border-radius:4px; font-size:0.90em; width:97%;">
<code class="language-python">
some_code(<span style="background:#fff3a3; padding:0 2px;">highlighted_part</span>)
</code></pre>
```

### Non-negotiable rules

| ✅ Must | ❌ Don't |
|---|---|
| Every `<div>` / `<pre>` block has `width:97%;` | Use `margin-right` (VSCode ignores it) |
| Use horizontal padding `24px` (10/12/20px vertical OK) | Use the old `padding:12px 16px;` (too tight) |
| Keep proper nouns in English (AIMessage, ToolNode, etc.) | Translate everything literally |
| Every emoji must have meaning | Decorative emoji |
| Long para → table or bulleted list | Wall of text |

### Filename convention

| Pattern | Meaning | Example |
|---|---|---|
| `N_a_🔥_*.ipynb` | Main lesson (the original from LangChain Academy) | `0_a_🔥_create_agent.ipynb` |
| `N_X_⭐️_*.ipynb` | Supplementary explanation (X = b,c,d,e...) | `2_d_⭐️_messages_完整执行轨迹.ipynb` |
| `_*.md` | Meta files (prompts, logs) | `_PROMPT_notebook_beautify.md` |

When adding a new explanation for lesson N, pick the next unused letter. Current allocation:
- 0: a✓ b✓ c✓ d✓ → next is `0_e_⭐️_*`
- 1: a✓ b✓ c✓ d✓ → next is `1_e_⭐️_*`
- 2: a✓ b✓ c✓ d✓ e✓ → next is `2_f_⭐️_*`
- 3: a✓ b✓ → next is `3_c_⭐️_*`
- 4: c✓ d✓ → gaps at a, b (don't fill unless asked); next is `4_e_⭐️_*`

---

## 📖 Established Vocabulary (use these terms exactly)

| Chinese | English equivalent | Don't use |
|---|---|---|
| ReAct 循环 / 状态机 | ReAct loop | "反应模式" |
| 工具节点 | ToolNode | — |
| 注入(InjectedState/InjectedToolCallId) | injection | "传递" |
| 派单 / 派发 | delegate (to sub-agent) | — |
| 复述 / recitation | recitation (Manus term) | "重复" |
| 注意力开关 | attention switch | — |
| 自我提示工具 | self-prompt tool | — |
| context rot | context rot | "上下文腐烂" |
| 隔离 context | isolated context | — |
| 落盘 | persist to file | "存储" |
| 治忘 / 治挤 / 治乱 | (informal) | use these in summaries |
| 工具留口子,LLM 来填创意 | (signature phrase) | — |

---

## 🧠 Mental Models Already Taught (don't re-explain unless asked)

1. **ReAct = LangGraph state machine** between agent ↔ tools nodes; LLM is stateless
2. **InjectedState / InjectedToolCallId** — strip params from LLM-visible schema, inject at execution
3. **Command(update={...})** — for multi-field state updates; manually craft ToolMessage with tool_call_id
4. **Default reducer = replace; file_reducer = merge** — merge needed for parallel/sub-agent scenarios
5. **Tool call params = LLM-generated text**, NOT framework-extracted (Topics-to-cover example)
6. **TODO recitation** — Manus pattern, anti-context-rot via "self-reminder"
7. **Files = attention switch** — Save → Search → Read-Back
8. **Context isolation** — `state["messages"] = [{...description}]` is the soul-line
9. **Three weapons for three diseases** — TODO 治忘 / Files 治挤 / Subagents 治乱

---

## 🚨 Anti-Patterns (User Has Pushed Back On These)

| Pattern | User reaction |
|---|---|
| Padding fix for VSCode right-edge issue | "依旧不行" → eventually `width:97%` worked |
| First explanation of Topics-to-cover (mentioning "programmer-style log") | "自相矛盾" |
| Saying "错误信息要写得像给程序员看的提示" | Contradicted "不是给人看的" claim |
| Saying file_reducer is needed for sequential writes | User correctly identified it's only needed for parallel |
| Generic phrases like "接下来我们将…" | Cut by user request |

---

## 💻 Useful Bash Commands (verified working in this env)

```bash
# List notebooks
cd "/Users/bohaoli/Desktop/tuto/tuto_langchain/official/langchain-langgraph-langsmith/course-deep-agents-⏬👤/deep-agents-from-scratch/notebooks"
ls -1 *.ipynb

# Find a pattern in ipynb (remember JSON escaping)
grep -oE 'pattern' *.ipynb

# Pattern: <div style=\"...border-radius:Xpx;\">  (note escaped quotes in JSON)
grep -oE '<div style=\\"[^\\]{0,200}border-radius:[0-9]+px;\\">' *.ipynb

# Bulk-edit divs (BSD sed for macOS)
sed -i '' -E 's|(<div style=\\"[^\\]*border-radius:[0-9]+px;)(\\">)|\1 margin-right:24px;\2|g' file.ipynb
# But prefer Write/Edit for clarity

# Check Python env
which python
python -c "import langgraph; print(langgraph.__file__)"

# uv commands
uv sync
uv run jupyter notebook
```

---

## 🛠️ Tool Behavior Notes

- **NotebookEdit** — must Read the .ipynb first or it errors with "File has not been read yet"
- **Path casing matters** — `/Users/bohaoli/Desktop/` (capital D), not `/desktop/`
- **ipynb files are JSON** — quotes are escaped as `\"`. When grepping for HTML inside, account for this
- **Markdown cells render in VSCode but quirky** — colored divs need `width:97%`, scrollbar covers right edge otherwise

---

## 📍 Where We Left Off

**Last completed task**: Generated 5 `_d_⭐️_本节精华.ipynb` summary notebooks (one per lesson) covering core mental models per lesson. Each follows the standard template:
1. Gradient title + 一句话定位
2. 核心收获 table (7-8 items)
3. Detailed mental model section
4. 设计精髓 (2-3 counterintuitive points)
5. 真实产品对应
6. ✨ Green-box 一句话带走

**Previous task before that**: Saved session log for human (`_session_log_2026-05-16.md`) and then user asked for agent-readable version (this file).

**No pending work items** — user can resume with anything: more analysis, more notebooks, debugging code cells, etc.

---

## 🎯 If User Asks You To...

| Request | Do this |
|---|---|
| "解释 X" / "我看不懂 X" | Use 2-3 angles: (1) core mechanism, (2) analogy, (3) verification/counterexample. Use established vocabulary above. |
| "把它放到 ipynb 里" | Use NotebookEdit. First Read the target file. Use established CSS templates with `width:97%`. |
| "生成一个新 ipynb" | Use Write with JSON content. Follow the structure of existing `⭐️` files. |
| "美化 / 重写 markdown" | Refer to `_PROMPT_notebook_beautify.md` for the full ruleset. |
| 代码或工具问题 | Don't assume — verify with bash/read first. User dislikes guesses that don't pan out. |

**Always**: respond in Chinese unless user explicitly asks for English. Match their terse, table-heavy style.

---

## 🔑 Three Phrases That Capture User's Style

1. **"避免冗长,避免重复"** — keep it tight
2. **"切中肯綮"** — go straight to the essence
3. **"言简意赅"** — concise but accurate

When in doubt, **prefer table to paragraph, bullet to sentence, code to description**.

---

**End of brief. Agent: proceed with user's next request using this context.**
