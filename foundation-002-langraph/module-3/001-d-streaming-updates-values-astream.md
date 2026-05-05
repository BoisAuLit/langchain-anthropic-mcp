因为你用的是：

```python
graph.astream_events(...)
```

它不是普通的 “stream 最终回答”。

它是：

> **把 LangGraph / LangChain 运行过程中所有底层事件都 stream 出来。**

所以它会非常长。

你贴出来的 output 里主要有这几类事件：

```text
on_chain_start
on_chat_model_start
on_chat_model_stream
on_chat_model_end
on_chain_end
```

---

最关键的是这一行反复出现：

```text
Node: conversation. Type: on_chat_model_stream. Name: ChatOpenAI
```

它为什么出现这么多次？

因为 `on_chat_model_stream` 是 **模型 token streaming 事件**。

模型不是一次性吐出完整回答，而是类似这样：

```text
chunk 1: "The"
chunk 2: " San"
chunk 3: " Francisco"
chunk 4: " 49ers"
chunk 5: " are"
...
```

每生成一点点，就触发一次：

```text
on_chat_model_stream
```

所以如果回答比较长，比如 “Tell me about the 49ers NFL team”，模型可能生成几百个小 chunk，于是你就看到几百行：

```text
on_chat_model_stream
on_chat_model_stream
on_chat_model_stream
...
```

---

你的代码现在打印的是事件 metadata：

```python
print(
    f"Node: {event['metadata'].get('langgraph_node', '')}. "
    f"Type: {event['event']}. "
    f"Name: {event['name']}"
)
```

所以每个 token chunk 都打印一行。

这就是 output 爆长的原因。

---

可以这样理解：

```text
graph.astream_events
= 全量运行日志

graph.stream(..., stream_mode="updates")
= 每个 node 返回了什么

graph.stream(..., stream_mode="values")
= 每一步之后完整 state 是什么

graph.astream_events
= node 开始、模型开始、模型每个 token、模型结束、node 结束、graph 结束
```

---

你的这次运行大概是：

```text
LangGraph start
↓
conversation node start
↓
ChatOpenAI start
↓
ChatOpenAI stream chunk 1
↓
ChatOpenAI stream chunk 2
↓
ChatOpenAI stream chunk 3
↓
...
↓
ChatOpenAI end
↓
should_continue start
↓
should_continue end
↓
conversation node stream
↓
conversation node end
↓
LangGraph stream
↓
LangGraph end
```

---

所以它长，不是因为 graph 循环了。

而是因为：

> **一个 ChatOpenAI 调用内部产生了很多 stream chunk events。**

---

如果你只想看最终 AIMessage，不要用 `astream_events`。

用：

```python
async for chunk in graph.astream(
    {"messages": [input_message]},
    config,
    stream_mode="updates",
):
    print(chunk)
```

如果你还是想用 `astream_events`，但不想看到这么多 token chunk，可以过滤掉：

```python
async for event in graph.astream_events(
    {"messages": [input_message]},
    config,
    version="v2",
):
    if event["event"] == "on_chat_model_stream":
        continue

    print(
        f"Node: {event['metadata'].get('langgraph_node', '')}. "
        f"Type: {event['event']}. "
        f"Name: {event['name']}"
    )
```

这样输出会短很多。
