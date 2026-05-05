“**Failure mode**” 是工程、软件、AI、机械、产品设计里非常常见的一个词。

中文通常翻译成：

* **失效模式**（最正式、最专业）
* **故障模式**
* **失败模式**（口语里也有人这么说）

---

## 先用最直白的话理解

你可以把它理解成：

> **“一个系统可能会以哪些方式出问题？”**

不是问：

> “它会不会坏？”

而是问：

> **“它具体会怎么坏？”**

也就是：

> **可能失败的方式（ways to fail）**

---

## 举几个例子

### 1）汽车 🚗

如果一辆车“失败（fail）”了，failure modes 可能有：

* 电池没电
* 发动机过热
* 刹车失灵
* 轮胎爆胎
* 油泵故障

这些每一种：

> 都是一种 **failure mode（失效模式）**

---

### 2）写代码 / 后端 API

假设你写了一个 API：

可能的 failure modes：

* 网络 timeout（超时）
* 数据库连接失败
* 返回格式错误
* JSON parsing error
* authentication failed（认证失败）
* memory leak（内存泄漏）

所以你设计系统时会问：

> “What are the failure modes?”

意思是：

> **“这个系统可能会以哪些方式挂掉？”**

---

### 3）AI Agent（你最近在学的这个特别相关）

比如一个 LangGraph agent workflow：

```
User → Planner → Tool → Memory → Final Answer
```

可能的 failure modes：

#### ① Planner 出错

Agent 理解错用户意图。

比如：

用户问：

> “帮我查 RBC 的 tax documents”

Agent 理解成：

> “帮我查 RBC stock price”

这是一种：

> **intent misunderstanding failure mode（意图理解错误）**

---

#### ② Tool selection 出错

应该调用 search tool，却调用 calculator。

这是一种：

> **tool selection failure mode（工具选择错误）**

---

#### ③ Hallucination

工具没返回结果，但 agent 自己编。

这是一种：

> **hallucination failure mode（幻觉型失效）**

---

#### ④ Infinite loop

agent 一直：

```
think → tool → think → tool
```

永远不结束。

这是一种：

> **looping failure mode（死循环失效）**

---

#### ⑤ Context overflow

上下文太长，前面重要信息被截断。

这是一种：

> **context window failure mode**

---

## 在大厂里为什么老提 failure modes？

因为高级工程师不是只问：

> “代码能跑吗？”

而是问：

> **“它在真实世界里会怎么死？”**

比如：

“如果 API timeout 怎么办？”

“如果 tool 返回空怎么办？”

“如果用户输入恶意 prompt 怎么办？”

“如果 LLM 输出 malformed JSON 怎么办？”

这些其实都在：

> **提前分析 failure modes**

---

## 在 AI Agent 时代，failure mode analysis 非常重要

你以后做 agentic systems（你想去硅谷，这个很 relevant），设计 workflow 时经常要问：

> “这个 graph 的 failure modes 是什么？”

例如在 LangChain / LangGraph 里，你可以从这几个角度分析：

| Layer         | 常见 failure modes                     |
| ------------- | ------------------------------------ |
| LLM           | hallucination, wrong reasoning       |
| Tool          | timeout, wrong tool, schema mismatch |
| Memory        | stale memory, missing memory         |
| Retrieval     | bad chunks, irrelevant docs          |
| Graph         | deadlock, infinite loop              |
| Human-in-loop | human never responds                 |

这就是：

> **systematic failure mode analysis（系统性失效分析）**

你以后做 production agent，这个能力比“会写 demo”重要很多。
