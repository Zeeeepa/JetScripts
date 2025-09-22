from datetime import datetime
from datetime import timedelta
from jet.logger import logger
from langchain_superlinked import SuperlinkedRetriever
import os
import shutil
import superlinked.framework as sl


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
# SuperlinkedRetriever Examples

This notebook demonstrates how to build a Superlinked App and Query Descriptor and use them with the LangChain `SuperlinkedRetriever`.

Install the integration from PyPI:

```bash
pip install -U langchain-superlinked superlinked
```

## Setup

Install the integration and its peer dependency:

```bash
pip install -U langchain-superlinked superlinked
```

## Instantiation

See below for creating a Superlinked App (`sl_client`) and a `QueryDescriptor` (`sl_query`), then wiring them into `SuperlinkedRetriever`.

## Usage

Call `retriever.invoke(query_text, **params)` to retrieve `Document` objects. Examples below show single-space and multi-space setups.

## Use within a chain

The retriever can be used in LangChain chains by piping it into your prompt and model. See the main Superlinked retriever page for a full RAG example.

## API reference

Refer to the API docs:

- https://python.langchain.com/api_reference/superlinked/retrievers/langchain_superlinked.retrievers.SuperlinkedRetriever.html
"""
logger.info("# SuperlinkedRetriever Examples")



class DocumentSchema(sl.Schema):
    id: sl.IdField
    content: sl.String


doc_schema = DocumentSchema()

text_space = sl.TextSimilaritySpace(
    text=doc_schema.content, model="sentence-transformers/all-MiniLM-L6-v2"
)
doc_index = sl.Index([text_space])

query = (
    sl.Query(doc_index)
    .find(doc_schema)
    .similar(text_space.text, sl.Param("query_text"))
    .select([doc_schema.content])
    .limit(sl.Param("limit"))
)

source = sl.InMemorySource(schema=doc_schema)
executor = sl.InMemoryExecutor(sources=[source], indices=[doc_index])
app = executor.run()

source.put(
    [
        {"id": "1", "content": "Machine learning algorithms process data efficiently."},
        {
            "id": "2",
            "content": "Natural language processing understands human language.",
        },
        {"id": "3", "content": "Deep learning models require significant compute."},
    ]
)

retriever = SuperlinkedRetriever(
    sl_client=app, sl_query=query, page_content_field="content"
)

retriever.invoke("artificial intelligence", limit=2)

class BlogPostSchema(sl.Schema):
    id: sl.IdField
    title: sl.String
    content: sl.String
    category: sl.String
    published_date: sl.Timestamp


blog = BlogPostSchema()

content_space = sl.TextSimilaritySpace(
    text=blog.content, model="sentence-transformers/all-MiniLM-L6-v2"
)
title_space = sl.TextSimilaritySpace(
    text=blog.title, model="sentence-transformers/all-MiniLM-L6-v2"
)
cat_space = sl.CategoricalSimilaritySpace(
    category_input=blog.category, categories=["technology", "science", "business"]
)
recency_space = sl.RecencySpace(
    timestamp=blog.published_date,
    period_time_list=[
        sl.PeriodTime(timedelta(days=30)),
        sl.PeriodTime(timedelta(days=90)),
    ],
)

blog_index = sl.Index([content_space, title_space, cat_space, recency_space])

blog_query = (
    sl.Query(
        blog_index,
        weights={
            content_space: sl.Param("content_weight"),
            title_space: sl.Param("title_weight"),
            cat_space: sl.Param("category_weight"),
            recency_space: sl.Param("recency_weight"),
        },
    )
    .find(blog)
    .similar(content_space.text, sl.Param("query_text"))
    .select([blog.title, blog.content, blog.category, blog.published_date])
    .limit(sl.Param("limit"))
)

source = sl.InMemorySource(schema=blog)
app = sl.InMemoryExecutor(sources=[source], indices=[blog_index]).run()


source.put(
    [
        {
            "id": "p1",
            "title": "Intro to ML",
            "content": "Machine learning 101",
            "category": "technology",
            "published_date": int((datetime.now() - timedelta(days=5)).timestamp()),
        },
        {
            "id": "p2",
            "title": "AI in Healthcare",
            "content": "Transforming diagnosis",
            "category": "science",
            "published_date": int((datetime.now() - timedelta(days=15)).timestamp()),
        },
    ]
)

blog_retriever = SuperlinkedRetriever(
    sl_client=app,
    sl_query=blog_query,
    page_content_field="content",
    metadata_fields=["title", "category", "published_date"],
)

blog_retriever.invoke(
    "machine learning", content_weight=1.0, recency_weight=0.5, limit=2
)

logger.info("\n\n[DONE]", bright=True)