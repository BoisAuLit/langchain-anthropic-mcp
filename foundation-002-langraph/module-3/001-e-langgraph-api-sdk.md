这个 notebook **二者兼具**，但分成两个阶段：

## 前半部分：只用 LangGraph library，没有 API / SDK

从 cell 5 到 cell 18，主要是：

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
```

然后直接：

```python
graph.stream(...)
graph.astream_events(...)
```

这里是**本地 Python 里直接运行 graph object**。

所以这一部分是：

> **LangGraph library 本地调用**
>
> 不是 LangGraph API
> 也不是 LangGraph SDK

---

## 后半部分：同时用到了 LangGraph API + LangGraph SDK

从 cell 19 开始，标题就是：

```text
Streaming with LangGraph API
```

关键代码：

```python
from langgraph_sdk import get_client

URL = "http://127.0.0.1:2024"
client = get_client(url=URL)
```

这里说明：

### 1. LangGraph API

你需要先在 terminal 运行：

```bash
langgraph dev
```

它会启动本地 API server：

```text
http://127.0.0.1:2024
```

这个就是：

> **LangGraph API 本地服务端**

---

### 2. LangGraph SDK

notebook 里用：

```python
client = get_client(url=URL)
```

然后：

```python
await client.assistants.search()
await client.threads.create()
client.runs.stream(...)
```

这些都是：

> **LangGraph SDK 客户端代码**

SDK 去调用本地的 LangGraph API。

---

## 最简单判断方式

看这两种写法：

### 写法 1：本地 graph object

```python
graph.stream(...)
graph.astream_events(...)
```

这是：

> **LangGraph library**

---

### 写法 2：client 调用

```python
client.threads.create()
client.runs.stream(...)
```

这是：

> **LangGraph SDK 调用 LangGraph API**

---

## 这个 notebook 的结构

```text
前半部分：
你自己在 notebook 里定义 graph
↓
直接 graph.stream(...)
↓
LangGraph library 本地运行


后半部分：
terminal 先运行 langgraph dev
↓
启动 LangGraph API server
↓
notebook 用 langgraph_sdk get_client()
↓
client 调用 API
```

所以最终答案是：

> **这个 notebook 前半部分没有用 API/SDK；后半部分同时用了 LangGraph API 和 LangGraph SDK。**

更准确地说：

> **LangGraph API 是被 `langgraph dev` 启动的本地服务；LangGraph SDK 是 notebook 里 `from langgraph_sdk import get_client` 创建出来的 client。**
