from jet.llm.mlx.base import MLX
from jet.logger import CustomLogger
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.memory import ChatMemoryBuffer
import openai
import os
import shutil


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
log_file = os.path.join(OUTPUT_DIR, "main.log")
logger = CustomLogger(log_file, overwrite=True)
logger.info(f"Logs: {log_file}")

"""
<a href="https://colab.research.google.com/github/run-llama/llama_index/blob/main/docs/docs/examples/chat_engine/chat_engine_context.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# Chat Engine - Context Mode

ContextChatEngine is a simple chat mode built on top of a retriever over your data.

For each chat interaction:
* first retrieve text from the index using the user message
* set the retrieved text as context in the system prompt
* return an answer to the user message

This approach is simple, and works for questions directly related to the knowledge base and general interactions.

If you're opening this Notebook on colab, you will probably need to install LlamaIndex 🦙.
"""
logger.info("# Chat Engine - Context Mode")

# %pip install llama-index-llms-ollama

# !pip install llama-index

"""
## Download Data
"""
logger.info("## Download Data")

# !mkdir -p 'data/paul_graham/'
# !wget 'https://raw.githubusercontent.com/run-llama/llama_index/main/docs/docs/examples/data/paul_graham/paul_graham_essay.txt' -O 'data/paul_graham/paul_graham_essay.txt'

"""
## Get started in 5 lines of code

Load data and build index
"""
logger.info("## Get started in 5 lines of code")


# os.environ["OPENAI_API_KEY"] = "API_KEY_HERE"
# openai.api_key = os.environ["OPENAI_API_KEY"]


data = SimpleDirectoryReader(input_dir="/Users/jethroestrada/Desktop/External_Projects/Jet_Projects/JetScripts/data/jet-resume/data/").load_data()
index = VectorStoreIndex.from_documents(data)

"""
Configure chat engine

Since the context retrieved can take up a large amount of the available LLM context, let's ensure we configure a smaller limit to the chat history!
"""
logger.info("Configure chat engine")


memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "You are a chatbot, able to have normal interactions, as well as talk"
        " about an essay discussing Paul Grahams life."
    ),
)

"""
Chat with your data
"""
logger.info("Chat with your data")

response = chat_engine.chat("Hello!")

logger.debug(response)

"""
Ask a follow up question
"""
logger.info("Ask a follow up question")

response = chat_engine.chat("What did Paul Graham do growing up?")

logger.debug(response)

response = chat_engine.chat("Can you tell me more?")

logger.debug(response)

"""
Reset conversation state
"""
logger.info("Reset conversation state")

chat_engine.reset()

response = chat_engine.chat("Hello! What do you know?")

logger.debug(response)

"""
## Streaming Support
"""
logger.info("## Streaming Support")


llm = MLX(model="qwen3-0.6b-4bit", log_dir=f"{OUTPUT_DIR}/chats", temperature=0)
data = SimpleDirectoryReader(input_dir="/Users/jethroestrada/Desktop/External_Projects/Jet_Projects/JetScripts/data/jet-resume/data/").load_data()

index = VectorStoreIndex.from_documents(data)

chat_engine = index.as_chat_engine(chat_mode="context", llm=llm)

response = chat_engine.stream_chat("What did Paul Graham do after YC?")
for token in response.response_gen:
    logger.debug(token, end="")

logger.info("\n\n[DONE]", bright=True)