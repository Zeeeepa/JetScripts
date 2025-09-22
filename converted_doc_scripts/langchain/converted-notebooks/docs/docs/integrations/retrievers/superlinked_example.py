from datetime import datetime
from datetime import datetime, timedelta
from jet.adapters.langchain.chat_ollama import ChatOllama
from jet.logger import logger
from langchain import hub
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_superlinked import SuperlinkedRetriever
from typing import Optional, List, Dict, Any
# import ChatModelTabs from "@theme/ChatModelTabs";
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
---
sidebar_label: SuperlinkedRetriever
---

# SuperlinkedRetriever

> [Superlinked](https://github.com/superlinked/superlinked) is a library for building context-aware vector search applications. It provides multi-modal vector spaces that can handle text similarity, categorical similarity, recency, and numerical values with flexible weighting strategies.

This will help you get started with the SuperlinkedRetriever [retriever](/docs/concepts/retrievers/). For detailed documentation of all SuperlinkedRetriever features and configurations head to the [API reference](https://python.langchain.com/api_reference/superlinked/retrievers/langchain_superlinked.retrievers.SuperlinkedRetriever.html).

### Further reading

- External article: [Build RAG using LangChain & Superlinked](https://links.superlinked.com/langchain_article)
- Integration repo: [superlinked/langchain-superlinked](https://github.com/superlinked/langchain-superlinked)
- Superlinked core repo: [superlinked/superlinked](https://links.superlinked.com/langchain_repo_sl)

### Integration details

| Retriever | Source | Package |
| :--- | :--- | :---: |
[SuperlinkedRetriever](https://python.langchain.com/api_reference/superlinked/retrievers/langchain_superlinked.retrievers.SuperlinkedRetriever.html) | Multi-modal vector search | langchain-superlinked |

## Setup

The SuperlinkedRetriever requires the `langchain-superlinked` package and its peer dependency `superlinked`. You can install these with:

```bash
pip install -U langchain-superlinked superlinked
```

No API keys are required for basic usage as Superlinked can run in-memory or with local vector databases.
"""
logger.info("# SuperlinkedRetriever")



"""
### App and Query: what the retriever needs

The retriever requires:

- `sl_client`: a Superlinked App created by an executor's `.run()`
- `sl_query`: a `QueryDescriptor` built via `sl.Query(...).find(...).similar(...).select(...).limit(...)`

Minimal example:

```python

class Doc(sl.Schema):
    id: sl.IdField
    content: sl.String

doc = Doc()
space = sl.TextSimilaritySpace(text=doc.content, model="sentence-transformers/all-MiniLM-L6-v2")
index = sl.Index([space])

query = (
    sl.Query(index)
    .find(doc)
    .similar(space.text, sl.Param("query_text"))
    .select([doc.content])
    .limit(sl.Param("limit"))
)

source = sl.InMemorySource(schema=doc)
app = sl.InMemoryExecutor(sources=[source], indices=[index]).run()

retriever = SuperlinkedRetriever(sl_client=app, sl_query=query, page_content_field="content")
```

For a production setup, create the executor with a vector DB (e.g., Qdrant) and pass it as `vector_database=...` before calling `.run()`.

## Instantiation
"""
logger.info("### App and Query: what the retriever needs")



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

documents = [
    {
        "id": "doc1",
        "content": "Machine learning algorithms can process large datasets efficiently.",
    },
    {
        "id": "doc2",
        "content": "Natural language processing enables computers to understand human language.",
    },
    {
        "id": "doc3",
        "content": "Deep learning models require significant computational resources.",
    },
    {
        "id": "doc4",
        "content": "Artificial intelligence is transforming various industries.",
    },
    {
        "id": "doc5",
        "content": "Neural networks are inspired by biological brain structures.",
    },
]

source = sl.InMemorySource(schema=doc_schema)
executor = sl.InMemoryExecutor(sources=[source], indices=[doc_index])
app = executor.run()
source.put(documents)

retriever = SuperlinkedRetriever(
    sl_client=app, sl_query=query, page_content_field="content", k=3
)

"""
## Usage
"""
logger.info("## Usage")

results = retriever.invoke("artificial intelligence and machine learning", limit=2)
for i, doc in enumerate(results, 1):
    logger.debug(f"Document {i}:")
    logger.debug(f"Content: {doc.page_content}")
    logger.debug(f"Metadata: {doc.metadata}")
    logger.debug("---")

more_results = retriever.invoke("neural networks and deep learning", k=4)
logger.debug(f"Retrieved {len(more_results)} documents:")
for i, doc in enumerate(more_results, 1):
    logger.debug(f"{i}. {doc.page_content[:50]}...")

"""
## Use within a chain

Like other retrievers, SuperlinkedRetriever can be incorporated into LLM applications via [chains](/docs/how_to/sequence/).

We will need a LLM or chat model:


<ChatModelTabs customVarName="llm" />
"""
logger.info("## Use within a chain")

# import getpass

# if not os.environ.get("OPENAI_API_KEY"):
#     os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your Ollama API key: ")


llm = ChatOllama(model="llama3.2")


prompt = hub.pull("rlm/rag-prompt")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

rag_chain.invoke("What is machine learning and how does it work?")

"""
## API reference

For detailed documentation of all SuperlinkedRetriever features and configurations, head to the [API reference](https://python.langchain.com/api_reference/superlinked/retrievers/langchain_superlinked.retrievers.SuperlinkedRetriever.html).

"""
logger.info("## API reference")
"""
SuperlinkedRetriever Usage Examples

This file demonstrates how to use the SuperlinkedRetriever with different
space configurations to showcase its flexibility across various use cases.
"""



def example_1_simple_text_search():
    """
    Example 1: Simple text-based semantic search
    Use case: Basic document retrieval based on content similarity
    """
    logger.debug("=== Example 1: Simple Text Search ===")

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

    documents = [
        {
            "id": "doc1",
            "content": "Machine learning algorithms can process large datasets efficiently.",
        },
        {
            "id": "doc2",
            "content": "Natural language processing enables computers to understand human language.",
        },
        {
            "id": "doc3",
            "content": "Deep learning models require significant computational resources.",
        },
        {
            "id": "doc4",
            "content": "Data science combines statistics, programming, and domain expertise.",
        },
        {
            "id": "doc5",
            "content": "Artificial intelligence is transforming various industries.",
        },
    ]

    source = sl.InMemorySource(schema=doc_schema)
    executor = sl.InMemoryExecutor(sources=[source], indices=[doc_index])
    app = executor.run()

    source.put(documents)

    retriever = SuperlinkedRetriever(
        sl_client=app, sl_query=query, page_content_field="content"
    )

    results = retriever.invoke("artificial intelligence and machine learning", limit=3)

    logger.debug(f"Query: 'artificial intelligence and machine learning'")
    logger.debug(f"Found {len(results)} documents:")
    for i, doc in enumerate(results, 1):
        logger.debug(f"  {i}. {doc.page_content}")
    logger.debug()


def example_2_multi_space_blog_search():
    """
    Example 2: Multi-space blog post search
    Use case: Blog search with content, category, and recency
    """
    logger.debug("=== Example 2: Multi-Space Blog Search ===")

    class BlogPostSchema(sl.Schema):
        id: sl.IdField
        title: sl.String
        content: sl.String
        category: sl.String
        published_date: sl.Timestamp
        view_count: sl.Integer

    blog_schema = BlogPostSchema()

    content_space = sl.TextSimilaritySpace(
        text=blog_schema.content, model="sentence-transformers/all-MiniLM-L6-v2"
    )

    title_space = sl.TextSimilaritySpace(
        text=blog_schema.title, model="sentence-transformers/all-MiniLM-L6-v2"
    )

    category_space = sl.CategoricalSimilaritySpace(
        category_input=blog_schema.category,
        categories=["technology", "science", "business", "health", "travel"],
    )

    recency_space = sl.RecencySpace(
        timestamp=blog_schema.published_date,
        period_time_list=[
            sl.PeriodTime(timedelta(days=30)),  # Last month
            sl.PeriodTime(timedelta(days=90)),  # Last 3 months
            sl.PeriodTime(timedelta(days=365)),  # Last year
        ],
    )

    popularity_space = sl.NumberSpace(
        number=blog_schema.view_count,
        min_value=0,
        max_value=10000,
        mode=sl.Mode.MAXIMUM,
    )

    blog_index = sl.Index(
        [content_space, title_space, category_space, recency_space, popularity_space]
    )

    blog_query = (
        sl.Query(
            blog_index,
            weights={
                content_space: sl.Param("content_weight"),
                title_space: sl.Param("title_weight"),
                category_space: sl.Param("category_weight"),
                recency_space: sl.Param("recency_weight"),
                popularity_space: sl.Param("popularity_weight"),
            },
        )
        .find(blog_schema)
        .similar(content_space.text, sl.Param("query_text"))
        .select(
            [
                blog_schema.title,
                blog_schema.content,
                blog_schema.category,
                blog_schema.published_date,
                blog_schema.view_count,
            ]
        )
        .limit(sl.Param("limit"))
    )


    blog_posts = [
        {
            "id": "post1",
            "title": "Introduction to Machine Learning",
            "content": "Machine learning is revolutionizing how we process data and make predictions.",
            "category": "technology",
            "published_date": int((datetime.now() - timedelta(days=5)).timestamp()),
            "view_count": 1500,
        },
        {
            "id": "post2",
            "title": "The Future of AI in Healthcare",
            "content": "Artificial intelligence is transforming medical diagnosis and treatment.",
            "category": "health",
            "published_date": int((datetime.now() - timedelta(days=15)).timestamp()),
            "view_count": 2300,
        },
        {
            "id": "post3",
            "title": "Business Analytics with Python",
            "content": "Learn how to use Python for business data analysis and visualization.",
            "category": "business",
            "published_date": int((datetime.now() - timedelta(days=45)).timestamp()),
            "view_count": 980,
        },
        {
            "id": "post4",
            "title": "Deep Learning Neural Networks",
            "content": "Understanding neural networks and their applications in modern AI.",
            "category": "technology",
            "published_date": int((datetime.now() - timedelta(days=2)).timestamp()),
            "view_count": 3200,
        },
    ]

    source = sl.InMemorySource(schema=blog_schema)
    executor = sl.InMemoryExecutor(sources=[source], indices=[blog_index])
    app = executor.run()

    source.put(blog_posts)

    retriever = SuperlinkedRetriever(
        sl_client=app,
        sl_query=blog_query,
        page_content_field="content",
        metadata_fields=["title", "category", "published_date", "view_count"],
    )

    scenarios = [
        {
            "name": "Content-focused search",
            "params": {
                "content_weight": 1.0,
                "title_weight": 0.3,
                "category_weight": 0.1,
                "recency_weight": 0.2,
                "popularity_weight": 0.1,
                "limit": 3,
            },
        },
        {
            "name": "Recent posts prioritized",
            "params": {
                "content_weight": 0.5,
                "title_weight": 0.2,
                "category_weight": 0.1,
                "recency_weight": 1.0,
                "popularity_weight": 0.1,
                "limit": 3,
            },
        },
        {
            "name": "Popular posts with category emphasis",
            "params": {
                "content_weight": 0.6,
                "title_weight": 0.3,
                "category_weight": 0.8,
                "recency_weight": 0.3,
                "popularity_weight": 0.9,
                "limit": 3,
            },
        },
    ]

    query_text = "machine learning and AI applications"

    for scenario in scenarios:
        logger.debug(f"\n--- {scenario['name']} ---")
        logger.debug(f"Query: '{query_text}'")

        results = retriever.invoke(query_text, **scenario["params"])

        for i, doc in enumerate(results, 1):
            logger.debug(
                f"  {i}. {doc.metadata['title']} (Category: {doc.metadata['category']}, Views: {doc.metadata['view_count']})"
            )

    logger.debug()


def example_3_ecommerce_product_search():
    """
    Example 3: E-commerce product search
    Use case: Product search with price range, brand preference, and ratings
    """
    logger.debug("=== Example 3: E-commerce Product Search ===")

    class ProductSchema(sl.Schema):
        id: sl.IdField
        name: sl.String
        description: sl.String
        brand: sl.String
        price: sl.Float
        rating: sl.Float
        category: sl.String

    product_schema = ProductSchema()

    description_space = sl.TextSimilaritySpace(
        text=product_schema.description, model="sentence-transformers/all-MiniLM-L6-v2"
    )

    name_space = sl.TextSimilaritySpace(
        text=product_schema.name, model="sentence-transformers/all-MiniLM-L6-v2"
    )

    brand_space = sl.CategoricalSimilaritySpace(
        category_input=product_schema.brand,
        categories=["Apple", "Samsung", "Sony", "Nike", "Adidas", "Canon"],
    )

    category_space = sl.CategoricalSimilaritySpace(
        category_input=product_schema.category,
        categories=["electronics", "clothing", "sports", "photography"],
    )

    price_space = sl.NumberSpace(
        number=product_schema.price,
        min_value=10.0,
        max_value=2000.0,
        mode=sl.Mode.MINIMUM,  # Favor lower prices
    )

    rating_space = sl.NumberSpace(
        number=product_schema.rating,
        min_value=1.0,
        max_value=5.0,
        mode=sl.Mode.MAXIMUM,  # Favor higher ratings
    )

    product_index = sl.Index(
        [
            description_space,
            name_space,
            brand_space,
            category_space,
            price_space,
            rating_space,
        ]
    )

    product_query = (
        sl.Query(
            product_index,
            weights={
                description_space: sl.Param("description_weight"),
                name_space: sl.Param("name_weight"),
                brand_space: sl.Param("brand_weight"),
                category_space: sl.Param("category_weight"),
                price_space: sl.Param("price_weight"),
                rating_space: sl.Param("rating_weight"),
            },
        )
        .find(product_schema)
        .similar(description_space.text, sl.Param("query_text"))
        .select(
            [
                product_schema.name,
                product_schema.description,
                product_schema.brand,
                product_schema.price,
                product_schema.rating,
                product_schema.category,
            ]
        )
        .limit(sl.Param("limit"))
    )

    products = [
        {
            "id": "prod1",
            "name": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation and long battery life.",
            "brand": "Sony",
            "price": 299.99,
            "rating": 4.5,
            "category": "electronics",
        },
        {
            "id": "prod2",
            "name": "Professional DSLR Camera",
            "description": "Full-frame DSLR camera perfect for professional photography and videography.",
            "brand": "Canon",
            "price": 1299.99,
            "rating": 4.8,
            "category": "photography",
        },
        {
            "id": "prod3",
            "name": "Running Shoes",
            "description": "Comfortable running shoes with excellent cushioning and support for athletes.",
            "brand": "Nike",
            "price": 129.99,
            "rating": 4.3,
            "category": "sports",
        },
        {
            "id": "prod4",
            "name": "Smartphone with 5G",
            "description": "Latest smartphone with 5G connectivity, advanced camera, and all-day battery.",
            "brand": "Samsung",
            "price": 899.99,
            "rating": 4.6,
            "category": "electronics",
        },
        {
            "id": "prod5",
            "name": "Bluetooth Speaker",
            "description": "Portable Bluetooth speaker with waterproof design and rich sound quality.",
            "brand": "Sony",
            "price": 79.99,
            "rating": 4.2,
            "category": "electronics",
        },
    ]

    source = sl.InMemorySource(schema=product_schema)
    executor = sl.InMemoryExecutor(sources=[source], indices=[product_index])
    app = executor.run()

    source.put(products)

    retriever = SuperlinkedRetriever(
        sl_client=app,
        sl_query=product_query,
        page_content_field="description",
        metadata_fields=["name", "brand", "price", "rating", "category"],
    )

    scenarios = [
        {
            "name": "Quality-focused search (high ratings matter most)",
            "query": "wireless audio device",
            "params": {
                "description_weight": 0.7,
                "name_weight": 0.5,
                "brand_weight": 0.2,
                "category_weight": 0.3,
                "price_weight": 0.1,
                "rating_weight": 1.0,  # Prioritize high ratings
                "limit": 3,
            },
        },
        {
            "name": "Budget-conscious search (price matters most)",
            "query": "electronics device",
            "params": {
                "description_weight": 0.6,
                "name_weight": 0.4,
                "brand_weight": 0.1,
                "category_weight": 0.2,
                "price_weight": 1.0,  # Prioritize lower prices
                "rating_weight": 0.3,
                "limit": 3,
            },
        },
        {
            "name": "Brand-focused search (brand loyalty)",
            "query": "sony products",
            "params": {
                "description_weight": 0.5,
                "name_weight": 0.3,
                "brand_weight": 1.0,  # Prioritize specific brand
                "category_weight": 0.2,
                "price_weight": 0.2,
                "rating_weight": 0.4,
                "limit": 3,
            },
        },
    ]

    for scenario in scenarios:
        logger.debug(f"\n--- {scenario['name']} ---")
        logger.debug(f"Query: '{scenario['query']}'")

        results = retriever.invoke(scenario["query"], **scenario["params"])

        for i, doc in enumerate(results, 1):
            metadata = doc.metadata
            logger.debug(
                f"  {i}. {metadata['name']} ({metadata['brand']}) - ${metadata['price']} - ⭐{metadata['rating']}"
            )

    logger.debug()


def example_4_news_article_search():
    """
    Example 4: News article search with sentiment and topics
    Use case: News search with content, sentiment, topic categorization, and recency
    """
    logger.debug("=== Example 4: News Article Search ===")

    class NewsArticleSchema(sl.Schema):
        id: sl.IdField
        headline: sl.String
        content: sl.String
        topic: sl.String
        sentiment_score: sl.Float  # -1 (negative) to 1 (positive)
        published_at: sl.Timestamp
        source: sl.String

    news_schema = NewsArticleSchema()

    content_space = sl.TextSimilaritySpace(
        text=news_schema.content, model="sentence-transformers/all-MiniLM-L6-v2"
    )

    headline_space = sl.TextSimilaritySpace(
        text=news_schema.headline, model="sentence-transformers/all-MiniLM-L6-v2"
    )

    topic_space = sl.CategoricalSimilaritySpace(
        category_input=news_schema.topic,
        categories=[
            "technology",
            "politics",
            "business",
            "sports",
            "entertainment",
            "science",
        ],
    )

    source_space = sl.CategoricalSimilaritySpace(
        category_input=news_schema.source,
        categories=["Reuters", "BBC", "CNN", "TechCrunch", "Bloomberg"],
    )

    sentiment_space = sl.NumberSpace(
        number=news_schema.sentiment_score,
        min_value=-1.0,
        max_value=1.0,
        mode=sl.Mode.MAXIMUM,  # Default to preferring positive news
    )

    recency_space = sl.RecencySpace(
        timestamp=news_schema.published_at,
        period_time_list=[
            sl.PeriodTime(timedelta(hours=6)),  # Last 6 hours
            sl.PeriodTime(timedelta(days=1)),  # Last day
            sl.PeriodTime(timedelta(days=7)),  # Last week
        ],
    )

    news_index = sl.Index(
        [
            content_space,
            headline_space,
            topic_space,
            source_space,
            sentiment_space,
            recency_space,
        ]
    )

    news_query = (
        sl.Query(
            news_index,
            weights={
                content_space: sl.Param("content_weight"),
                headline_space: sl.Param("headline_weight"),
                topic_space: sl.Param("topic_weight"),
                source_space: sl.Param("source_weight"),
                sentiment_space: sl.Param("sentiment_weight"),
                recency_space: sl.Param("recency_weight"),
            },
        )
        .find(news_schema)
        .similar(content_space.text, sl.Param("query_text"))
        .select(
            [
                news_schema.headline,
                news_schema.content,
                news_schema.topic,
                news_schema.sentiment_score,
                news_schema.published_at,
                news_schema.source,
            ]
        )
        .limit(sl.Param("limit"))
    )

    news_articles = [
        {
            "id": "news1",
            "headline": "Major Breakthrough in AI Research Announced",
            "content": "Scientists have developed a new artificial intelligence model that shows remarkable improvements in natural language understanding.",
            "topic": "technology",
            "sentiment_score": 0.8,
            "published_at": int((datetime.now() - timedelta(hours=2)).timestamp()),
            "source": "TechCrunch",
        },
        {
            "id": "news2",
            "headline": "Stock Market Faces Volatility Amid Economic Concerns",
            "content": "Financial markets experienced significant fluctuations today as investors react to new economic data and policy announcements.",
            "topic": "business",
            "sentiment_score": -0.3,
            "published_at": int((datetime.now() - timedelta(hours=8)).timestamp()),
            "source": "Bloomberg",
        },
        {
            "id": "news3",
            "headline": "New Climate Research Shows Promising Results",
            "content": "Recent studies indicate that innovative climate technologies are showing positive environmental impact and could help address climate change.",
            "topic": "science",
            "sentiment_score": 0.6,
            "published_at": int((datetime.now() - timedelta(hours=12)).timestamp()),
            "source": "Reuters",
        },
        {
            "id": "news4",
            "headline": "Tech Companies Report Strong Quarterly Earnings",
            "content": "Several major technology companies exceeded expectations in their quarterly earnings reports, driven by AI and cloud computing growth.",
            "topic": "technology",
            "sentiment_score": 0.7,
            "published_at": int((datetime.now() - timedelta(hours=4)).timestamp()),
            "source": "CNN",
        },
    ]

    source = sl.InMemorySource(schema=news_schema)
    executor = sl.InMemoryExecutor(sources=[source], indices=[news_index])
    app = executor.run()

    source.put(news_articles)

    retriever = SuperlinkedRetriever(
        sl_client=app,
        sl_query=news_query,
        page_content_field="content",
        metadata_fields=[
            "headline",
            "topic",
            "sentiment_score",
            "published_at",
            "source",
        ],
    )

    logger.debug(f"Query: 'artificial intelligence developments'")

    results = retriever.invoke(
        "artificial intelligence developments",
        content_weight=0.8,
        headline_weight=0.6,
        topic_weight=0.4,
        source_weight=0.2,
        sentiment_weight=0.3,
        recency_weight=1.0,  # Prioritize recent news
        limit=2,
    )

    logger.debug("\nRecent Technology News:")
    for i, doc in enumerate(results, 1):
        metadata = doc.metadata
        published_timestamp = metadata["published_at"]
        published_time = datetime.fromtimestamp(published_timestamp)
        hours_ago = (datetime.now() - published_time).total_seconds() / 3600
        sentiment = (
            "📈 Positive"
            if metadata["sentiment_score"] > 0
            else "📉 Negative"
            if metadata["sentiment_score"] < 0
            else "➡️ Neutral"
        )

        logger.debug(f"  {i}. {metadata['headline']}")
        logger.debug(f"     Source: {metadata['source']} | {sentiment} | {hours_ago:.1f}h ago")

    logger.debug()


def demonstrate_langchain_integration():
    """
    Example 5: Integration with LangChain RAG pipeline
    Shows how to use the SuperlinkedRetriever in a complete RAG workflow
    """
    logger.debug("=== Example 5: LangChain RAG Integration ===")


    class FAQSchema(sl.Schema):
        id: sl.IdField
        question: sl.String
        answer: sl.String
        category: sl.String

    faq_schema = FAQSchema()

    text_space = sl.TextSimilaritySpace(
        text=faq_schema.question, model="sentence-transformers/all-MiniLM-L6-v2"
    )

    category_space = sl.CategoricalSimilaritySpace(
        category_input=faq_schema.category,
        categories=["technical", "billing", "general", "account"],
    )

    faq_index = sl.Index([text_space, category_space])

    faq_query = (
        sl.Query(
            faq_index,
            weights={
                text_space: sl.Param("text_weight"),
                category_space: sl.Param("category_weight"),
            },
        )
        .find(faq_schema)
        .similar(text_space.text, sl.Param("query_text"))
        .select([faq_schema.question, faq_schema.answer, faq_schema.category])
        .limit(sl.Param("limit"))
    )

    faqs = [
        {
            "id": "faq1",
            "question": "How do I reset my password?",
            "answer": "You can reset your password by clicking 'Forgot Password' on the login page and following the email instructions.",
            "category": "account",
        },
        {
            "id": "faq2",
            "question": "Why is my API not working?",
            "answer": "Check your API key, rate limits, and ensure you're using the correct endpoint URL.",
            "category": "technical",
        },
        {
            "id": "faq3",
            "question": "How do I upgrade my subscription?",
            "answer": "Visit the billing section in your account settings to upgrade your plan.",
            "category": "billing",
        },
    ]

    source = sl.InMemorySource(schema=faq_schema)
    executor = sl.InMemoryExecutor(sources=[source], indices=[faq_index])
    app = executor.run()

    source.put(faqs)

    retriever = SuperlinkedRetriever(
        sl_client=app,
        sl_query=faq_query,
        page_content_field="answer",
        metadata_fields=["question", "category"],
    )

    user_question = "I can't access the API"

    logger.debug(f"User Question: '{user_question}'")
    logger.debug("Retrieving relevant context...")

    context_docs = retriever.invoke(
        user_question, text_weight=1.0, category_weight=0.3, limit=2
    )

    logger.debug("\nRetrieved Context:")
    for i, doc in enumerate(context_docs, 1):
        logger.debug(f"  {i}. Q: {doc.metadata['question']}")
        logger.debug(f"     A: {doc.page_content}")
        logger.debug(f"     Category: {doc.metadata['category']}")

    logger.debug(
        "\n[In a real RAG setup, this context would be passed to an LLM to generate a response]"
    )
    logger.debug()


def example_6_qdrant_vector_database():
    """
    Example 6: Same retriever with Qdrant vector database
    Use case: Production deployment with persistent vector storage

    This demonstrates that SuperlinkedRetriever is vector database agnostic.
    The SAME retriever code works with Qdrant (or Redis, MongoDB) by only
    changing the executor configuration, not the retriever implementation.
    """
    logger.debug("=== Example 6: Qdrant Vector Database ===")

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

    logger.debug("🔧 Configuring Qdrant vector database...")
    try:
        qdrant_vector_db = sl.QdrantVectorDatabase(
            url="https://your-qdrant-cluster.qdrant.io",  # Replace with your Qdrant URL
            # Replace with your API key
            default_query_limit=10,
            vector_precision=sl.Precision.FLOAT16,
        )
        logger.debug("Qdrant configuration created (credentials needed for actual connection)")
    except Exception as e:
        logger.debug(f"Qdrant not configured (expected without credentials): {e}")
        logger.debug("Using in-memory fallback for demonstration...")
        qdrant_vector_db = None

    documents = [
        {
            "id": "doc1",
            "content": "Machine learning algorithms can process large datasets efficiently.",
        },
        {
            "id": "doc2",
            "content": "Natural language processing enables computers to understand human language.",
        },
        {
            "id": "doc3",
            "content": "Deep learning models require significant computational resources.",
        },
        {
            "id": "doc4",
            "content": "Data science combines statistics, programming, and domain expertise.",
        },
        {
            "id": "doc5",
            "content": "Artificial intelligence is transforming various industries.",
        },
    ]

    source = sl.InMemorySource(schema=doc_schema)

    if qdrant_vector_db:
        executor = sl.InMemoryExecutor(
            sources=[source],
            indices=[doc_index],
            vector_database=qdrant_vector_db,  # This makes it use Qdrant!
        )
        storage_type = "Qdrant (persistent)"
    else:
        executor = sl.InMemoryExecutor(sources=[source], indices=[doc_index])
        storage_type = "In-Memory (fallback)"

    app = executor.run()

    source.put(documents)

    retriever = SuperlinkedRetriever(
        sl_client=app, sl_query=query, page_content_field="content"
    )

    results = retriever.invoke("artificial intelligence and machine learning", limit=3)

    logger.debug(f"Vector Storage: {storage_type}")
    logger.debug(f"Query: 'artificial intelligence and machine learning'")
    logger.debug(f"Found {len(results)} documents:")
    for i, doc in enumerate(results, 1):
        logger.debug(f"  {i}. {doc.page_content}")

    logger.debug(
        "\nKey Insight: Same SuperlinkedRetriever code works with any vector database!"
    )
    logger.debug(
        "Only executor configuration changes, retriever implementation stays identical"
    )
    logger.debug("Switch between in-memory → Qdrant → Redis → MongoDB without code changes")
    logger.debug()


def main():
    """
    Run all examples to demonstrate the flexibility of SuperlinkedRetriever
    """
    logger.debug("SuperlinkedRetriever Examples")
    logger.debug("=" * 50)
    logger.debug("This file demonstrates how the SuperlinkedRetriever can be used")
    logger.debug("with different space configurations for various use cases.\n")

    try:
        example_1_simple_text_search()
        example_2_multi_space_blog_search()
        example_3_ecommerce_product_search()
        example_4_news_article_search()
        demonstrate_langchain_integration()
        example_6_qdrant_vector_database()

        logger.debug("All examples completed successfully!")

    except Exception as e:
        logger.debug(f"Error running examples: {e}")
        logger.debug("Make sure you have 'superlinked' package installed:")
        logger.debug("pip install superlinked")

logger.info("\n\n[DONE]", bright=True)