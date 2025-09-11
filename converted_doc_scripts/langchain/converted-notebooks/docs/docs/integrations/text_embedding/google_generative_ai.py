from jet.logger import logger
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import os
import shutil
import { ItemTable } from "@theme/FeatureTables";


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
---
sidebar_label: Google Gemini
keywords: [google gemini embeddings]
---

# Google Generative AI Embeddings (AI Studio & Gemini API)

Connect to Google's generative AI embeddings service using the `GoogleGenerativeAIEmbeddings` class, found in the [langchain-google-genai](https://pypi.org/project/langchain-google-genai/) package.

This will help you get started with Google's Generative AI embedding models (like Gemini) using LangChain. For detailed documentation on `GoogleGenerativeAIEmbeddings` features and configuration options, please refer to the [API reference](https://python.langchain.com/v0.2/api_reference/google_genai/embeddings/langchain_google_genai.embeddings.GoogleGenerativeAIEmbeddings.html).

## Overview
### Integration details


<ItemTable category="text_embedding" item="Google Gemini" />

## Setup

To access Google Generative AI embedding models you'll need to create a Google Cloud project, enable the Generative Language API, get an API key, and install the `langchain-google-genai` integration package.

### Credentials

To use Google Generative AI models, you must have an API key. You can create one in Google AI Studio. See the [Google documentation](https://ai.google.dev/gemini-api/docs/api-key) for instructions.

Once you have a key, set it as an environment variable `GOOGLE_API_KEY`:
"""
logger.info("# Google Generative AI Embeddings (AI Studio & Gemini API)")

# import getpass

if not os.getenv("GOOGLE_API_KEY"):
#     os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key: ")

"""
To enable automated tracing of your model calls, set your [LangSmith](https://docs.smith.langchain.com/) API key:
"""
logger.info("To enable automated tracing of your model calls, set your [LangSmith](https://docs.smith.langchain.com/) API key:")



"""
## Installation
"""
logger.info("## Installation")

# %pip install --upgrade --quiet  langchain-google-genai

"""
## Usage
"""
logger.info("## Usage")


embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector = embeddings.embed_query("hello, world!")
vector[:5]

"""
## Batch

You can also embed multiple strings at once for a processing speedup:
"""
logger.info("## Batch")

vectors = embeddings.embed_documents(
    [
        "Today is Monday",
        "Today is Tuesday",
        "Today is April Fools day",
    ]
)
len(vectors), len(vectors[0])

"""
## Indexing and Retrieval

Embedding models are often used in retrieval-augmented generation (RAG) flows, both as part of indexing data as well as later retrieving it. For more detailed instructions, please see our [RAG tutorials](/docs/tutorials/rag).

Below, see how to index and retrieve data using the `embeddings` object we initialized above. In this example, we will index and retrieve a sample document in the `InMemoryVectorStore`.
"""
logger.info("## Indexing and Retrieval")


text = "LangChain is the framework for building context-aware reasoning applications"

vectorstore = InMemoryVectorStore.from_texts(
    [text],
    embedding=embeddings,
)

retriever = vectorstore.as_retriever()

retrieved_documents = retriever.invoke("What is LangChain?")

retrieved_documents[0].page_content

"""
## Task type
`GoogleGenerativeAIEmbeddings` optionally support a `task_type`, which currently must be one of:

- `SEMANTIC_SIMILARITY`: Used to generate embeddings that are optimized to assess text similarity.
- `CLASSIFICATION`: Used to generate embeddings that are optimized to classify texts according to preset labels.
- `CLUSTERING`: Used to generate embeddings that are optimized to cluster texts based on their similarities.
- `RETRIEVAL_DOCUMENT`, `RETRIEVAL_QUERY`, `QUESTION_ANSWERING`, and `FACT_VERIFICATION`: Used to generate embeddings that are optimized for document search or information retrieval.
- `CODE_RETRIEVAL_QUERY`: Used to retrieve a code block based on a natural language query, such as sort an array or reverse a linked list. Embeddings of the code blocks are computed using `RETRIEVAL_DOCUMENT`.

By default, we use `RETRIEVAL_DOCUMENT` in the `embed_documents` method and `RETRIEVAL_QUERY` in the `embed_query` method. If you provide a task type, we will use that for all methods.
"""
logger.info("## Task type")

# %pip install --upgrade --quiet  matplotlib scikit-learn


query_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", task_type="RETRIEVAL_QUERY"
)
doc_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", task_type="RETRIEVAL_DOCUMENT"
)

q_embed = query_embeddings.embed_query("What is the capital of France?")
d_embed = doc_embeddings.embed_documents(
    ["The capital of France is Paris.", "Philipp is likes to eat pizza."]
)

for i, d in enumerate(d_embed):
    logger.debug(f"Document {i + 1}:")
    logger.debug(f"Cosine similarity with query: {cosine_similarity([q_embed], [d])[0][0]}")
    logger.debug("---")

"""
## API Reference

For detailed documentation on `GoogleGenerativeAIEmbeddings` features and configuration options, please refer to the [API reference](https://python.langchain.com/api_reference/google_genai/embeddings/langchain_google_genai.embeddings.GoogleGenerativeAIEmbeddings.html).

## Additional Configuration

You can pass the following parameters to ChatGoogleGenerativeAI in order to customize the SDK's behavior:

- `client_options`: [Client Options](https://googleapis.dev/python/google-api-core/latest/client_options.html#module-google.api_core.client_options) to pass to the Google API Client, such as a custom `client_options["api_endpoint"]`
- `transport`: The transport method to use, such as `rest`, `grpc`, or `grpc_asyncio`.
"""
logger.info("## API Reference")

logger.info("\n\n[DONE]", bright=True)