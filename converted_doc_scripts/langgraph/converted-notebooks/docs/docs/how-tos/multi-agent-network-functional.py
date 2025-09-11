from jet.adapters.langchain.chat_ollama import ChatOllama
from jet.logger import logger
from langchain_core.messages import AIMessage
from langchain_core.messages import convert_to_messages
from langchain_core.tools import tool
from langgraph.func import entrypoint
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages
from langgraph.prebuilt import create_react_agent
from typing_extensions import Literal
import os
import random
import shutil


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
log_file = os.path.join(OUTPUT_DIR, "main.log")
logger.basicConfig(filename=log_file)
logger.info(f"Logs: {log_file}")

PERSIST_DIR = f"{OUTPUT_DIR}/chroma"
os.makedirs(PERSIST_DIR, exist_ok=True)

"""
# How to build a multi-agent network (functional API)

!!! info "Prerequisites" 
    This guide assumes familiarity with the following:

    - [Multi-agent systems](../../concepts/multi_agent)
    - [Functional API](../../concepts/functional_api)
    - [Command](../../concepts/low_level/#command)
    - [LangGraph Glossary](../../concepts/low_level/)

In this how-to guide we will demonstrate how to implement a [multi-agent network](../../concepts/multi_agent#network) architecture where each agent can communicate with every other agent (many-to-many connections) and can decide which agent to call next. We will be using [functional API](../../concepts/functional_api) — individual agents will be defined as tasks and the agent handoffs will be defined in the main [entrypoint()][langgraph.func.entrypoint]:

```python


# Define a tool to signal intent to hand off to a different agent
@tool(return_direct=True)
def transfer_to_hotel_advisor():
    """
logger.info("# How to build a multi-agent network (functional API)")Ask hotel advisor agent for help."""
    return "Successfully transferred to hotel advisor"


# define an agent
travel_advisor_tools = [transfer_to_hotel_advisor, ...]
travel_advisor = create_react_agent(model, travel_advisor_tools)


# define a task that calls an agent
@task
def call_travel_advisor(messages):
    response = travel_advisor.invoke({"messages": messages})
    return response["messages"]


# define the multi-agent network workflow
@entrypoint()
def workflow(messages):
    call_active_agent = call_travel_advisor
    while True:
        agent_messages = call_active_agent(messages).result()
        messages = messages + agent_messages
        call_active_agent = get_next_agent(messages)
    return messages
```

## Setup

First, let's install the required packages
"""
logger.info("# define an agent")

# %%capture --no-stderr
# %pip install -U langgraph langchain-anthropic

# import getpass


# def _set_env(var: str):
#     if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")


# _set_env("ANTHROPIC_API_KEY")

"""
<div class="admonition tip">
    <p class="admonition-title">Set up <a href="https://smith.langchain.com">LangSmith</a> for LangGraph development</p>
    <p style="padding-top: 5px;">
        Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started <a href="https://docs.smith.langchain.com">here</a>. 
    </p>
</div>

## Travel agent example

In this example we will build a team of travel assistant agents that can communicate with each other.

We will create 2 agents:

* `travel_advisor`: can help with travel destination recommendations. Can ask `hotel_advisor` for help.
* `hotel_advisor`: can help with hotel recommendations. Can ask `travel_advisor` for help.

This is a fully-connected network - every agent can talk to any other agent.

First, let's create some of the tools that the agents will be using:
"""
logger.info("## Travel agent example")


@tool
def get_travel_recommendations():
    """Get recommendation for travel destinations"""
    return random.choice(["aruba", "turks and caicos"])


@tool
def get_hotel_recommendations(location: Literal["aruba", "turks and caicos"]):
    """Get hotel recommendations for a given destination."""
    return {
        "aruba": [
            "The Ritz-Carlton, Aruba (Palm Beach)"
            "Bucuti & Tara Beach Resort (Eagle Beach)"
        ],
        "turks and caicos": ["Grace Bay Club", "COMO Parrot Cay"],
    }[location]


@tool(return_direct=True)
def transfer_to_hotel_advisor():
    """Ask hotel advisor agent for help."""
    return "Successfully transferred to hotel advisor"


@tool(return_direct=True)
def transfer_to_travel_advisor():
    """Ask travel advisor agent for help."""
    return "Successfully transferred to travel advisor"


"""
!!! note "Transfer tools"

    You might have noticed that we're using `@tool(return_direct=True)` in the transfer tools. This is done so that individual agents (e.g., `travel_advisor`) can exit the ReAct loop early once these tools are called. This is the desired behavior, as we want to detect when the agent calls this tool and hand control off _immediately_ to a different agent. 
    
    **NOTE**: This is meant to work with the prebuilt [`create_react_agent`][langgraph.prebuilt.chat_agent_executor.create_react_agent] -- if you are building a custom agent, make sure to manually add logic for handling early exit for tools that are marked with `return_direct`.

Now let's define our agent tasks and combine them into a single multi-agent network workflow:
"""
logger.info("You might have noticed that we're using `@tool(return_direct=True)` in the transfer tools. This is done so that individual agents (e.g., `travel_advisor`) can exit the ReAct loop early once these tools are called. This is the desired behavior, as we want to detect when the agent calls this tool and hand control off _immediately_ to a different agent.")


model = ChatOllama(model="llama3.2")

travel_advisor_tools = [
    get_travel_recommendations,
    transfer_to_hotel_advisor,
]
travel_advisor = create_react_agent(
    model,
    travel_advisor_tools,
    prompt=(
        "You are a general travel expert that can recommend travel destinations (e.g. countries, cities, etc). "
        "If you need hotel recommendations, ask 'hotel_advisor' for help. "
        "You MUST include human-readable response before transferring to another agent."
    ),
)


@task
def call_travel_advisor(messages):
    response = travel_advisor.invoke({"messages": messages})
    return response["messages"]


hotel_advisor_tools = [get_hotel_recommendations, transfer_to_travel_advisor]
hotel_advisor = create_react_agent(
    model,
    hotel_advisor_tools,
    prompt=(
        "You are a hotel expert that can provide hotel recommendations for a given destination. "
        "If you need help picking travel destinations, ask 'travel_advisor' for help."
        "You MUST include human-readable response before transferring to another agent."
    ),
)


@task
def call_hotel_advisor(messages):
    response = hotel_advisor.invoke({"messages": messages})
    return response["messages"]


@entrypoint()
def workflow(messages):
    messages = add_messages([], messages)

    call_active_agent = call_travel_advisor
    while True:
        agent_messages = call_active_agent(messages).result()
        messages = add_messages(messages, agent_messages)
        ai_msg = next(m for m in reversed(agent_messages)
                      if isinstance(m, AIMessage))
        if not ai_msg.tool_calls:
            break

        tool_call = ai_msg.tool_calls[-1]
        if tool_call["name"] == "transfer_to_travel_advisor":
            call_active_agent = call_travel_advisor
        elif tool_call["name"] == "transfer_to_hotel_advisor":
            call_active_agent = call_hotel_advisor
        else:
            raise ValueError(
                f"Expected transfer tool, got '{tool_call['name']}'")

    return messages


"""
Lastly, let's define a helper to render the agent outputs:
"""
logger.info("Lastly, let's define a helper to render the agent outputs:")


def pretty_print_messages(update):
    if isinstance(update, tuple):
        ns, update = update
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        logger.debug(f"Update from subgraph {graph_id}:")
        logger.debug("\n")

    for node_name, node_update in update.items():
        logger.debug(f"Update from node {node_name}:")
        logger.debug("\n")

        for m in convert_to_messages(node_update["messages"]):
            m.pretty_logger.debug()
        logger.debug("\n")


"""
Let's test it out using the same input as our original multi-agent system:
"""
logger.info(
    "Let's test it out using the same input as our original multi-agent system:")

for chunk in workflow.stream(
    [
        {
            "role": "user",
            "content": "i wanna go somewhere warm in the caribbean. pick one destination and give me hotel recommendations",
        }
    ],
    subgraphs=True,
):
    pretty_print_messages(chunk)

"""
Voila - `travel_advisor` picks a destination and then makes a decision to call `hotel_advisor` for more info!
"""
logger.info("Voila - `travel_advisor` picks a destination and then makes a decision to call `hotel_advisor` for more info!")

logger.info("\n\n[DONE]", bright=True)
