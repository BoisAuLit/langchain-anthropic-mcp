# Model Context Protocol (MCP) — Architecture Summary

> Source: https://modelcontextprotocol.io/docs/concepts/architecture

---

## 📌 Scope

The Model Context Protocol includes the following projects:

- **MCP Specification**: Outlines implementation requirements for clients and servers.
- **MCP SDKs**: Language-specific SDKs implementing MCP.
- **MCP Development Tools**: Tools for developing MCP servers and clients (e.g., MCP Inspector).
- **MCP Reference Server Implementations**: Reference implementations of MCP servers.

---

## 👥 Participants

MCP follows a **client-server architecture**:

| Participant   | Role |
|---------------|------|
| **MCP Host**  | The AI application (e.g., Claude Desktop, VS Code) that manages one or more MCP clients |
| **MCP Client**| A component that maintains a dedicated connection to one MCP server |
| **MCP Server**| A program that provides context (tools, resources, prompts) to MCP clients |

- **Local MCP servers** use **STDIO transport** and serve a single client.
- **Remote MCP servers** use **Streamable HTTP transport** and serve many clients.

---

## 🧱 Layers

MCP has **two layers**:

### 1. Data Layer (Inner Layer)
Defines the JSON-RPC 2.0-based protocol for communication:
- **Lifecycle management**: connection init, capability negotiation, termination
- **Server features**: tools, resources, prompts
- **Client features**: sampling, elicitation, logging
- **Utility features**: notifications, progress tracking

### 2. Transport Layer (Outer Layer)
Manages communication channels and authentication:
- **Stdio transport**: Standard I/O streams, local processes, no network overhead
- **Streamable HTTP transport**: HTTP POST + optional Server-Sent Events (SSE), supports OAuth, bearer tokens, API keys

---

## 🔄 Data Layer Protocol

### Lifecycle Management
- Negotiates capabilities between client and server
- Sequence: Initialize → Negotiate → Operate → Terminate

### Primitives

#### Server-side Primitives
| Primitive     | Description |
|---------------|-------------|
| **Tools**     | Executable functions (file ops, API calls, DB queries) |
| **Resources** | Data sources (file contents, DB records, API responses) |
| **Prompts**   | Reusable interaction templates (system prompts, few-shot examples) |

Each primitive supports:
- `*/list` — discover available primitives
- `*/get` — retrieve a specific primitive
- `tools/call` — execute a tool

#### Client-side Primitives
| Primitive       | Description |
|-----------------|-------------|
| **Sampling**    | Servers request LLM completions from the client (`sampling/createMessage`) |
| **Elicitation** | Servers request additional input from the user (`elicitation/create`) |
| **Logging**     | Servers send log messages to clients for debugging |

#### Cross-cutting Utility Primitives
| Primitive              | Description |
|------------------------|-------------|
| **Tasks** *(Experimental)* | Durable execution wrappers for deferred results and status tracking |

### Notifications
- Real-time JSON-RPC 2.0 notification messages (no response expected)
- Servers notify clients of changes (e.g., new or updated tools)

---

## 💡 Example Use Case

A database-context MCP server can expose:
- **Tool**: Query the database
- **Resource**: Database schema
- **Prompt**: Few-shot examples for interacting with the tools

VS Code (Host) → MCP Client (Sentry) → Sentry MCP Server (Remote/HTTP)  
VS Code (Host) → MCP Client (FS) → Filesystem MCP Server (Local/STDIO)
