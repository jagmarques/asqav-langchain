<p align="center">
  <a href="https://asqav.com">
    <img src="https://asqav.com/logo-text-white.png" alt="Asqav" width="200">
  </a>
</p>
<p align="center">
  Record tool activity as signed receipts.
</p>
<p align="center">
  <a href="https://www.asqav.com/">Website</a> |
  <a href="https://www.asqav.com/docs">Docs</a> |
  <a href="https://github.com/jagmarques/asqav-sdk">SDK</a>
</p>

# Asqav for LangChain and LangGraph

Record tool activity as signed receipts.

`asqav-langchain` connects [Asqav](https://asqav.com) to LangChain and LangGraph through a callback handler. It attempts to sign tool-start, tool-completion and tool-error events so a holder can check the resulting records.

The handler observes tool execution. A policy refusal, missing receipt or signing outage does not stop the tool: errors are logged and execution continues. Use a separate execution guard when an action must depend on authorization. This callback is not that guard.

Receipts cover events submitted through the integration. They do not establish that every action was observed or that the recorded event was true.

## Install

Install from this repository with the LangChain extra:

```bash
pip install "asqav-langchain[langchain] @ git+https://github.com/jagmarques/asqav-langchain.git"
```

The package uses `asqav` 0.10.10 and accepts compatible patch releases. The `[langchain]` extra installs `langchain-core`; no model-provider package is needed for the example below.

## Usage

Set `ASQAV_API_KEY` to your API key. This example invokes a LangChain tool and passes the handler through its callback configuration:

```python
import os

import asqav
from langchain_core.tools import tool

from asqav_langchain import AsqavCallbackHandler

asqav.init(api_key=os.environ["ASQAV_API_KEY"])
handler = AsqavCallbackHandler(agent_name="calculator")


@tool
def add_one(value: int) -> int:
    """Add one to a number."""
    return value + 1


result = add_one.invoke({"value": 2}, config={"callbacks": [handler]})
print(result)  # 3
```

An agent or LangGraph application can pass the same handler through the `callbacks` list on its runnable invocation. Tool execution triggers a start callback followed by a completion callback on success or an error callback on failure.

## How it works

`AsqavCallbackHandler` extends the Asqav adapter base class and LangChain's `BaseCallbackHandler`:

- `on_tool_start` submits the tool name and an input preview.
- `on_tool_end` submits output type and length.
- `on_tool_error` submits the error type and a message preview.

Input and error previews are truncated to 200 characters. Signing failures are logged without raising into the tool call. A successful tool result therefore does not prove a receipt was issued; retrieve and verify the records issued by the signing service.

## Data handling

The handler constructs event context and passes it to the Python SDK. In hash-only mode, the SDK hashes that context locally before sending the signing request. Payload mode sends the context to the configured service, including the input or error preview the callback collected.

Configure the SDK mode for your deployment:

```python
asqav.init(api_key=os.environ["ASQAV_API_KEY"], mode="hash-only")
```

## Configuration

```python
# Use an existing Asqav agent by ID
handler = AsqavCallbackHandler(agent_id="ag_abc123")

# Override the API key
handler = AsqavCallbackHandler(api_key="sk_other", agent_name="audit-agent")
```

## License

[Elastic License 2.0](LICENSE)
