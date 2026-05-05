`NodeInterrupt` 是 LangGraph 里一个非常重要、但初看很容易和：

* `interrupt_before`
* `interrupt_after`
* `thread`
* `checkpoint`

混在一起的概念。

我先给你一句最重要的话：

> **`interrupt_before` 是 graph 外部提前规定“在哪停”。**
>
> **`NodeInterrupt` 是 node 自己运行到一半，主动说“我要停”。**

这是最核心区别。

---

# 一、先看你已经学过的 interrupt_before

你刚才的：

```python
graph = builder.compile(
    interrupt_before=["tools"]
)
```

意思：

> graph 运行之前就说好了：

```text
“每次到 tools 前，都停。”
```

像高速收费站：

```text
每辆车都要停。
```

不管什么情况。

---

流程：

```text
assistant
↓
准备去 tools
↓
停
```

---

这是：

> **静态 interrupt**

提前配置。

---

# 二、NodeInterrupt 是什么？

NodeInterrupt 完全不同。

它不是 compile 时决定。

而是：

> **node 自己在 runtime 决定。**

像 node 内部说：

> “等一下，这个情况不对，我先暂停。”

---

比如：

```python
from langgraph.errors import NodeInterrupt
```

---

node：

```python
def payment_node(state):

    amount = state["amount"]

    if amount > 10000:
        raise NodeInterrupt(
            "Large payment requires approval"
        )

    return state
```

---

流程：

```text
payment node
↓
检查金额
↓
超过一万
↓
raise NodeInterrupt
↓
暂停
```

---

不是 graph 提前规定。

是：

> node 临场判断。

---

---

# 三、为什么需要 NodeInterrupt？

现实 agent 里，经常遇到：

不是所有情况都需要人工介入。

只有：

> 某些特殊条件。

比如：

---

## 例子1：部署生产环境

```text
if env == "prod":
```

暂停：

> “确认部署吗？”

---

## 例子2：发邮件

```text
if recipient_count > 1000:
```

暂停：

> “确认群发吗？”

---

## 例子3：花钱

```text
if cost > $500:
```

暂停：

> “确认购买吗？”

---

## 例子4：删除文件

```text
if delete_count > 100:
```

暂停。

---

所以：

NodeInterrupt 本质：

> **conditional human-in-the-loop**

---

# 四、和 interrupt_before 的本质区别

看这个表：

|         | interrupt_before | NodeInterrupt |
| ------- | ---------------- | ------------- |
| 谁决定停？   | graph            | node          |
| 什么时候决定？ | compile time     | runtime       |
| 是否看数据？  | 不看               | 看 state       |
| 灵活性     | 固定               | 很高            |

---

比如：

---

interrupt_before：

```python
interrupt_before=["payment"]
```

意思：

> 所有 payment 都停。

```text
$1
$10
$100
$10000
```

全停。

---

NodeInterrupt：

```python
if amount > 10000:
    raise NodeInterrupt()
```

意思：

```text
$1 → 继续
$10 → 继续
$100 → 继续
$10000 → 停
```

更智能。

---

# 五、 NodeInterrupt 发生后，内部发生了什么？

这是重点。

假设：

```python
thread_id="1"
```

运行：

---

step1：

```text
START
```

---

step2：

```text
assistant
```

checkpoint 保存。

---

step3：

进入：

```text
payment_node
```

---

node 里：

```python
raise NodeInterrupt(...)
```

---

LangGraph 会：

# 1. 保存 checkpoint

比如：

```text
checkpoint_3
```

---

# 2. 保存 interrupt metadata

比如：

```json
{
  "reason":"Large payment"
}
```

---

# 3. thread 保持 alive

thread 不会结束。

---

所以：

你可以 later resume。

---

---

# 六、resume 怎么工作？

暂停后：

你可能：

* UI 点 approve
* Slack 点 approve
* human review

然后：

继续：

```python
graph.stream(
    Command(resume=True),
    config
)
```

（新版 API 可能是 `Command(resume=...)`）

意思：

> 从上次 checkpoint 接着跑。

不是重跑。

---

流程：

```text
checkpoint 3
↓
resume
↓
payment node 后面继续
```

---

---

# 七、NodeInterrupt 和 thread 的关系（这个很重要）

你最近一直学 thread。

NodeInterrupt 必须依赖：

> **thread + checkpoint**

否则恢复不了。

---

因为：

暂停时：

LangGraph 必须知道：

> “哪条 timeline 停住了？”

比如：

```text
thread 1 paused
thread 2 running
thread 3 finished
```

---

所以：

NodeInterrupt 和 thread 是强绑定。

---

# 八、NodeInterrupt 和 super step 的关系

你前面学 super step。

如果 node 在某个 super step 里 interrupt：

整个 super step 会暂停。

比如：

```text
A
↓
B,C (parallel)
↓
D
```

如果：

B：

```python
raise NodeInterrupt()
```

那么：

super step 2 暂停。

checkpoint 保存。

等待 resume。

---

所以：

NodeInterrupt 不是“小异常”。

它会影响：

> **整个 graph scheduling**

这就是为什么它在 production 很值钱。

---

# 九、你做 bug-fix agent 时最实用的场景

结合你的 Playwright agent：

---

```text
detect bug
↓
generate fix
↓
git diff
↓
deploy
```

在 deploy node：

```python
if branch == "main":
    raise NodeInterrupt(
        "Deploying to main branch"
    )
```

---

然后：

Slack：

> Approve?

你点：

> Yes

继续。

---

这就是非常典型的 production 用法。

---

一句话记忆：

> **`interrupt_before` = “到这里统一停车。”**
>
> **`NodeInterrupt` = “node 根据现场情况，主动踩刹车。”**

如果你今天在 LangChain Academy 开始看到 `Command(resume=...)`、`graph.get_state(config)`、`state.tasks` 这些东西，那就是在围绕 `NodeInterrupt` 这套暂停/恢复机制展开。
