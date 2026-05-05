你可以这样理解：

```text
updates = 只看每个 node 刚刚返回了什么
values  = 看每一步之后完整 state 变成了什么
```

---

## 1. `stream_mode="updates"`

这个输出的是 **node 的返回值 delta**。

你的 graph 里 node 叫：

```python
conversation
```

所以输出长这样：

```python
{
    "conversation": {
        "messages": [AIMessage(...)]
    }
}
```

意思是：

```text
conversation 这个 node 刚刚返回了：
{"messages": [AIMessage(...)]}
```

它不是完整 state。

它只是告诉你：

> 这个 node 这一步更新了什么。

所以你可以这样取：

```python
for chunk in graph.stream(..., stream_mode="updates"):
    for msg in chunk["conversation"]["messages"]:
        msg.pretty_print()
```

这时只会打印 AI 回复，因为这个 node 只返回了 AIMessage。

---

## 2. `stream_mode="values"`

这个输出的是 **每一步之后的完整 state**。

所以第一次你看到：

```text
Human: hi! I'm Lance
```

这是刚把输入放进 state 后的状态。

然后 node 执行完以后，state 变成：

```text
Human: hi! I'm Lance
AI: Hello, Lance! ...
```

所以第二次打印：

```text
Human: hi! I'm Lance
AI: Hello, Lance! ...
```

因此 `values` 会看起来“重复打印 HumanMessage”，但它不是重复生成，而是因为每次打印的是完整 state。

---

## 对比

假设初始输入：

```python
messages = [HumanMessage("hi")]
```

`conversation` node 返回：

```python
{"messages": [AIMessage("hello")]}
```

最终 state：

```python
{"messages": [HumanMessage("hi"), AIMessage("hello")]}
```

那么：

### `updates`

看到的是：

```python
{
  "conversation": {
    "messages": [AIMessage("hello")]
  }
}
```

### `values`

看到的是：

第一次：

```python
{
  "messages": [HumanMessage("hi")]
}
```

第二次：

```python
{
  "messages": [
    HumanMessage("hi"),
    AIMessage("hello")
  ]
}
```

---

一句话：

> `updates` 适合看 **每个 node 输出了什么**。
> `values` 适合看 **整个 state 现在是什么样子**。
