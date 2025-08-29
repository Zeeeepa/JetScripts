from jet.llm.ollama.base_langchain import ChatOllama
from jet.logger import CustomLogger
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from langgraph.graph.message import add_messages
import os
import shutil


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
log_file = os.path.join(OUTPUT_DIR, "main.log")
logger = CustomLogger(log_file, overwrite=True)
logger.info(f"Logs: {log_file}")

"""
# How to create a ReAct agent from scratch (Functional API)

!!! info "Prerequisites"
    This guide assumes familiarity with the following:
    
    - [Chat Models](https://python.langchain.com/docs/concepts/chat_models)
    - [Messages](https://python.langchain.com/docs/concepts/messages)
    - [Tool Calling](https://python.langchain.com/docs/concepts/tool_calling/)
    - [Entrypoints](../../concepts/functional_api/#entrypoint) and [Tasks](../../concepts/functional_api/#task)

This guide demonstrates how to implement a ReAct agent using the LangGraph [Functional API](../../concepts/functional_api).

The ReAct agent is a [tool-calling agent](../../concepts/agentic_concepts/#tool-calling-agent) that operates as follows:

1. Queries are issued to a chat model;
2. If the model generates no [tool calls](../../concepts/agentic_concepts/#tool-calling), we return the model response.
3. If the model generates tool calls, we execute the tool calls with available tools, append them as [tool messages](https://python.langchain.com/docs/concepts/messages/) to our message list, and repeat the process.

This is a simple and versatile set-up that can be extended with memory, human-in-the-loop capabilities, and other features. See the dedicated [how-to guides](../../how-tos/#prebuilt-react-agent) for examples.

## Setup

First, let's install the required packages and set our API keys:
"""
logger.info("# How to create a ReAct agent from scratch (Functional API)")

# %%capture --no-stderr
# %pip install -U langgraph langchain-openai

# import getpass


def _set_env(var: str):
    if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")


# _set_env("OPENAI_API_KEY")

"""
<div class="admonition tip">
     <p class="admonition-title">Set up <a href="https://smith.langchain.com">LangSmith</a> for better debugging</p>
     <p style="padding-top: 5px;">
         Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM aps built with LangGraph — read more about how to get started in the <a href="https://docs.smith.langchain.com">docs</a>. 
     </p>
 </div>

## Create ReAct agent

Now that you have installed the required packages and set your environment variables, we can create our agent.

### Define model and tools

Let's first define the tools and model we will use for our example. Here we will use a single place-holder tool that gets a description of the weather for a location.

We will use an [Ollama](https://python.langchain.com/docs/integrations/providers/openai/) chat model for this example, but any model [supporting tool-calling](https://python.langchain.com/docs/integrations/chat/) will suffice.
"""
logger.info("## Create ReAct agent")


model = ChatOllama(model="llama3.2")


@tool
def get_weather(location: str):
    """Call to get the weather from a specific location."""
    if any([city in location.lower() for city in ["sf", "san francisco"]]):
        return "It's sunny!"
    elif "boston" in location.lower():
        return "It's rainy!"
    else:
        return f"I am not sure what the weather is in {location}"


tools = [get_weather]

"""
### Define tasks

We next define the [tasks](../../concepts/functional_api/#task) we will execute. Here there are two different tasks:

1. **Call model**: We want to query our chat model with a list of messages.
2. **Call tool**: If our model generates tool calls, we want to execute them.
"""
logger.info("### Define tasks")


tools_by_name = {tool.name: tool for tool in tools}


@task
def call_model(messages):
    """Call model with a sequence of messages."""
    response = model.bind_tools(tools).invoke(messages)
    return response


@task
def call_tool(tool_call):
    tool = tools_by_name[tool_call["name"]]
    observation = tool.invoke(tool_call["args"])
    return ToolMessage(content=observation, tool_call_id=tool_call["id"])

"""
### Define entrypoint

Our [entrypoint](../../concepts/functional_api/#entrypoint) will handle the orchestration of these two tasks. As described above, when our `call_model` task generates tool calls, the `call_tool` task will generate responses for each. We append all messages to a single messages list.

!!! tip
    Note that because tasks return future-like objects, the below implementation executes tools in parallel.
"""
logger.info("### Define entrypoint")



@entrypoint()
def agent(messages):
    llm_response = call_model(messages).result()
    while True:
        if not llm_response.tool_calls:
            break

        tool_result_futures = [
            call_tool(tool_call) for tool_call in llm_response.tool_calls
        ]
        tool_results = [fut.result() for fut in tool_result_futures]

        messages = add_messages(messages, [llm_response, *tool_results])

        llm_response = call_model(messages).result()

    return llm_response

"""
## Usage

To use our agent, we invoke it with a messages list. Based on our implementation, these can be LangChain [message](https://python.langchain.com/docs/concepts/messages/) objects or Ollama-style dicts:
"""
logger.info("## Usage")

user_message = {"role": "user", "content": "What's the weather in san francisco?"}
logger.debug(user_message)

for step in agent.stream([user_message]):
    for task_name, message in step.items():
        if task_name == "agent":
            continue  # Just print task updates
        logger.debug(f"\n{task_name}:")
        message.pretty_logger.debug()

"""
Perfect! The graph correctly calls the `get_weather` tool and responds to the user after receiving the information from the tool. Check out the LangSmith trace [here](https://smith.langchain.com/public/d5a0d5ea-bdaa-4032-911e-7db177c8141b/r).

## Add thread-level persistence

Adding [thread-level persistence](../../concepts/persistence#threads) lets us support conversational experiences with our agent: subsequent invocations will append to the prior messages list, retaining the full conversational context.

To add thread-level persistence to our agent:

1. Select a [checkpointer](../../concepts/persistence#checkpointer-libraries): here we will use [InMemorySaver](../../reference/checkpoints/#langgraph.checkpoint.memory.InMemorySaver), a simple in-memory checkpointer.
2. Update our entrypoint to accept the previous messages state as a second argument. Here, we simply append the message updates to the previous sequence of messages.
3. Choose which values will be returned from the workflow and which will be saved by the checkpointer as `previous` using `entrypoint.final` (optional)
"""
logger.info("## Add thread-level persistence")


checkpointer = InMemorySaver()


@entrypoint(checkpointer=checkpointer)
def agent(messages, previous):
    if previous is not None:
        messages = add_messages(previous, messages)

    llm_response = call_model(messages).result()
    while True:
        if not llm_response.tool_calls:
            break

        tool_result_futures = [
            call_tool(tool_call) for tool_call in llm_response.tool_calls
        ]
        tool_results = [fut.result() for fut in tool_result_futures]

        messages = add_messages(messages, [llm_response, *tool_results])

        llm_response = call_model(messages).result()

    messages = add_messages(messages, llm_response)
    return entrypoint.final(value=llm_response, save=messages)

"""
We will now need to pass in a config when running our application. The config will specify an identifier for the conversational thread.

!!! tip

    Read more about thread-level persistence in our [concepts page](../../concepts/persistence/) and [how-to guides](../../how-tos/#persistence).
"""
logger.info("We will now need to pass in a config when running our application. The config will specify an identifier for the conversational thread.")

config = {"configurable": {"thread_id": "1"}}

"""
We start a thread the same way as before, this time passing in the config:
"""
logger.info("We start a thread the same way as before, this time passing in the config:")

user_message = {"role": "user", "content": "What's the weather in san francisco?"}
logger.debug(user_message)

for step in agent.stream([user_message], config):
    for task_name, message in step.items():
        if task_name == "agent":
            continue  # Just print task updates
        logger.debug(f"\n{task_name}:")
        message.pretty_logger.debug()

"""
When we ask a follow-up conversation, the model uses the prior context to infer that we are asking about the weather:
"""
logger.info("When we ask a follow-up conversation, the model uses the prior context to infer that we are asking about the weather:")

user_message = {"role": "user", "content": "How does it compare to Boston, MA?"}
logger.debug(user_message)

for step in agent.stream([user_message], config):
    for task_name, message in step.items():
        if task_name == "agent":
            continue  # Just print task updates
        logger.debug(f"\n{task_name}:")
        message.pretty_logger.debug()

"""
In the [LangSmith trace](https://smith.langchain.com/public/20a1116b-bb3b-44c1-8765-7a28663439d9/r), we can see that the full conversational context is retained in each model call.
"""
logger.info("In the [LangSmith trace](https://smith.langchain.com/public/20a1116b-bb3b-44c1-8765-7a28663439d9/r), we can see that the full conversational context is retained in each model call.")

logger.info("\n\n[DONE]", bright=True)