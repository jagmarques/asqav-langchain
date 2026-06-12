<p align="center">
  <a href="https://asqav.com">
    <img src="https://asqav.com/logo-text-white.png" alt="Asqav" width="200">
  </a>
</p>
<p align="center">
  Stop a rogue agent before it acts, and prove what it tried.
</p>
<p align="center">
  <a href="https://www.asqav.com/">Website</a> |
  <a href="https://www.asqav.com/docs">Docs</a> |
  <a href="https://github.com/jagmarques/asqav-sdk">SDK</a>
</p>

# Asqav for LangChain and LangGraph

Stop a rogue agent before it acts, and prove what it tried.

`asqav-langchain` plugs [Asqav](https://asqav.com) into LangChain and LangGraph through a standard callback handler. Every tool your agent invokes produces a tamper-evident signed record of what it attempted, so you have cryptographic proof of agent behaviour for EU AI Act, DORA, and SOC 2 audits.

This integration uses LangChain's documented stable callback surface: `BaseCallbackHandler.on_tool_start`, `on_tool_end`, and `on_tool_error`. It observes and records, and it is fail-open: it never blocks tool execution itself. To stop a rogue agent before it acts, enforce policies on the Asqav side or use a gating integration such as the [MCP server](https://github.com/jagmarques/asqav-mcp).

Asqav governs the agents you wire through it. An agent that never routes through the governed path produces no receipt and is not detected.

## Install

Not yet on PyPI. Install from GitHub:

```bash
pip install "git+https://github.com/jagmarques/asqav-langchain.git#egg=asqav-langchain[langchain]"
```

LangChain is a peer dependency. If you already have `langchain` or `langchain-core` installed you can drop the `[langchain]` extra. If it is missing, the handler raises a clear `ImportError` telling you to install it.

## Usage

```python
import asqav
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

from asqav_langchain import AsqavCallbackHandler

asqav.init(api_key="sk_...")

handler = AsqavCallbackHandler(agent_name="my-agent")

llm = ChatOpenAI(model="gpt-4o")
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# Pass the handler through callbacks; it fires on every tool call.
executor.invoke(
    {"input": "Search for the latest AI news"},
    config={"callbacks": [handler]},
)
```

The same handler works with LangGraph. Pass it through the `callbacks` list on any graph or runnable invocation:

```python
graph.invoke(state, config={"callbacks": [AsqavCallbackHandler(agent_name="my-agent")]})
```

Every tool call produces signed `tool:start`, `tool:end`, and `tool:error` events through the Asqav API. Signing runs server-side with NIST FIPS 204 ML-DSA cryptography, so the audit trail stays tamper-evident.

## How it works

`AsqavCallbackHandler` extends both the Asqav adapter base class and LangChain's `BaseCallbackHandler`, overriding three callbacks:

- `on_tool_start` signs `tool:start` with the tool name and an input preview
- `on_tool_end` signs `tool:end` with output metadata
- `on_tool_error` signs `tool:error` with error details

All signing is fail-open. If the Asqav API is unreachable, a warning is logged but the tool call proceeds normally.

## Data handling

`asqav-langchain` is a thin wrapper around the `asqav` Python SDK and inherits its mode behaviour:

- **Asqav cloud on `*.asqav.com`:** the SDK hashes your action context locally and sends only the hash plus a small metadata bag. Raw prompts and tool arguments never leave your infrastructure.
- **Self-hosted:** the SDK sends the full context so the server can run policy checks, PII redaction, and richer audit views.

You can override per call:

```python
import asqav

asqav.init(api_key="sk_...", base_url="https://api.asqav.com", mode="hash-only")
```

## Configuration

```python
# Use an existing Asqav agent by ID
handler = AsqavCallbackHandler(agent_id="ag_abc123")

# Override the API key
handler = AsqavCallbackHandler(api_key="sk_other", agent_name="audit-agent")
```

## License

MIT
