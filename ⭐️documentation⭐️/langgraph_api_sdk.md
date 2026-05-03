好，这两个确实是整个 LangGraph 生态里**最容易混淆**的部分。

因为名字太像：

* LangGraph **API**
* LangGraph **SDK**

很多人第一反应：

> “API 不就是 SDK 吗？”

其实不是。

你可以先死记一句：

> **API = 服务端（server）**
>
> **SDK = 客户端（client）**

如果只记住这一句，已经赢一半了。

---

# 一、先用你最熟悉的东西类比：OpenAI

你天天用 OpenAI API，对吧？

你写：

```python
from openai import OpenAI

client = OpenAI()

client.responses.create(...)
```

这里：

你在用什么？

你在用：

> **OpenAI Python SDK**

不是 API。

SDK 帮你调用 API。

真正的 API 在云端：

```text
https://api.openai.com/v1/...
```

---

LangGraph 一模一样：

```text
LangGraph API ← 被调用
       ↑
LangGraph SDK ← 调用者
```

---

一句话：

> **API 被调用，SDK 去调用。**

---

# 二、LangGraph API 到底是什么？

官方说：

> runtime + queue + persistence

初学者看完基本更懵。

我给你翻译成人话：

> **LangGraph API = 一个专门帮你“管理 graph 生命周期”的后端服务。**

重点：

不是 graph。

是：

> graph manager。

---

比如你写了一个 bug-fix agent：

```text
detect_bug
   ↓
analyze_code
   ↓
fix_code
   ↓
run_test
   ↓
deploy
```

你 compile：

```python
graph = builder.compile()
```

现在 graph 只是：

> 内存里的一个 Python object。

只能：

```python
graph.invoke(...)
```

问题来了：

现实世界里会发生：

---

用户 A：

> 修复 bug #1

用户 B：

> 修复 bug #2

用户 C：

> 修复 bug #3

---

每个任务：

* 5 分钟
* 有 checkpoint
* 中间可能失败
* 可能要 resume

如果你只用：

```python
graph.invoke()
```

很快乱掉。

---

所以 LangGraph API 出现了：

它说：

> “graph 交给我，我帮你管理。”

---

它负责：

# 1）创建 thread

比如：

用户发起任务。

API：

```text
POST /threads
```

返回：

```json
{
  "thread_id":"abc123"
}
```

意思：

> “这个用户有自己的 timeline。”

---

你昨天问的 thread 就在这里。

---

# 2）创建 run

thread 创建后：

开始执行。

API：

```text
POST /runs
```

比如：

```json
{
  "thread_id":"abc123",
  "input":{
     "bug":"button broken"
  }
}
```

---

API：

> “收到，我放进队列。”

不是立刻执行。

---

# 3）任务队列

比如：

100 个用户同时来。

API：

```text
Run1
Run2
Run3
Run4
```

排队。

像：

* Celery
* RabbitMQ

---

所以：

API 不是单纯 HTTP server。

它是：

> **agent job manager**

---

# 4）保存 checkpoints

每个 super step 结束：

API 自动保存。

```text
Step1
↓
checkpoint1

Step2
↓
checkpoint2

Step3
↓
checkpoint3
```

---

保存在：

* sqlite
* postgres
* cloud db

---

所以：

程序 crash：

可以恢复。

---

# 5）恢复执行

比如：

Step 8 崩了。

你可以：

```text
resume thread abc123
```

API：

> “我有 checkpoint。”

继续。

---

---

# 用一句话总结 API

> **LangGraph API = graph 的操作系统。**

graph 是 app。

API 是 OS。

负责：

* scheduling
* state
* storage
* recovery
* concurrency

---

# 三、LangGraph SDK 是什么？

SDK 完全不同。

SDK 不管理 graph。

SDK 不保存 state。

SDK 不跑 graph。

SDK 只是：

> **远程控制器。**

---

就像：

你家电视。

---

电视：

= API

---

遥控器：

= SDK

---

你按：

```python
client.threads.create()
```

就像：

按：

```text
Power On
```

---

你按：

```python
client.runs.create()
```

就像：

```text
Play
```

---

电视自己播放。

遥控器不播放。

---

这个比喻非常重要。

---

# 四、SDK 到底干嘛？

比如你有：

前端：

* React

后端：

* FastAPI

CLI：

* Python script

---

都想调用你的 graph。

你不想：

自己写：

```python
requests.post(...)
```

所以 SDK 帮你包装。

---

原始 HTTP：

```python
requests.post(
   "http://localhost:2024/threads"
)
```

---

SDK：

```python
client.threads.create()
```

更优雅。

---

# 五、SDK 最常见操作

---

## 1. create thread

```python
thread = client.threads.create()
```

意思：

> 开一个新的 conversation。

---

返回：

```json
{
   "thread_id":"abc123"
}
```

---

## 2. run graph

```python
client.runs.create(...)
```

意思：

> 开始执行。

---

## 3. get state

```python
client.threads.get_state(...)
```

意思：

> 当前执行到哪里？

---

比如：

```json
{
  "current_node":"run_test"
}
```

---

## 4. replay

```python
client.runs.replay(...)
```

---

## 5. fork

```python
client.runs.fork(...)
```

---

---

# 六、真实调用链（最重要）

假设你的 bug-fix system：

```text
React dashboard
```

用户点：

> Fix Bug

---

前端：

调用 SDK：

```python
client.runs.create()
```

---

SDK：

发 HTTP：

```text
POST localhost:2024/runs
```

---

LangGraph API：

收到。

---

API：

启动 graph：

```text
detect
analyze
fix
test
deploy
```

---

API：

保存 checkpoints。

---

SDK：

轮询：

```python
client.state.get()
```

---

前端：

显示：

```text
Currently testing...
```

---

整个链路：

```text
Frontend
 ↓
SDK
 ↓
API
 ↓
Graph
 ↓
Checkpoint
```

---

# 七、为什么 LangGraph 要拆成 API + SDK？

因为 production 必须 client/server 分离。

否则：

你公司：

* React dashboard
* Slack bot
* Cron job
* Mobile app

都要：

```python
graph.invoke()
```

根本不现实。

---

拆开后：

所有客户端：

```text
React
Slack bot
CLI
FastAPI
```

统一：

用 SDK。

调用：

同一个 API。

---

这就是企业级 architecture。

---

如果用你熟悉的话说：

> **LangGraph = 业务流程**
>
> **LangGraph API = agent runtime server**
>
> **LangGraph SDK = agent remote controller**

你以后看 thread、run、assistant、checkpoint，脑子里都放到 **API 那边**；看到 `client.xxx()`，脑子里都放到 **SDK 那边**。这一下会清很多。
