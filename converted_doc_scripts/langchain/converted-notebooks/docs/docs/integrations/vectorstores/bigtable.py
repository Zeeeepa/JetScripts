from jet.transformers.formatters import format_json
from google.colab import auth
from jet.logger import logger
from langchain_core.documents import Document
from langchain_google_bigtable import BigtableEngine
from langchain_google_bigtable import BigtableVectorStore
from langchain_google_bigtable import ColumnConfig, VectorMetadataMapping, Encoding
from langchain_google_bigtable.vector_store import QueryParameters
from langchain_google_bigtable.vector_store import init_vector_store_table
from langchain_google_vertexai import VertexAIEmbeddings
import os
import shutil

async def main():
    
    
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
    sidebar_label: Google Bigtable
    ---
    
    # BigtableVectorStore
    
    This guide covers the `BigtableVectorStore` integration for using Google Cloud Bigtable as a vector store.
    
    [Bigtable](https://cloud.google.com/bigtable) is a key-value and wide-column store, ideal for fast access to structured, semi-structured, or unstructured data.
    
    ## Overview
    
    The `BigtableVectorStore` uses Google Cloud Bigtable to store documents and their vector embeddings for similarity search and retrieval. It supports powerful metadata filtering to refine search results.
    
    ### Integration details
    | Class | Package | Local | JS support | Package downloads | Package latest |
    | :--- | :--- | :---: | :---: | :---: | :---: |
    | [BigtableVectorStore](https://github.com/googleapis/langchain-google-bigtable-python/blob/main/src/langchain_google_bigtable/vector_store.py) | [langchain-google-bigtable](https://pypi.org/project/langchain-google-bigtable/) | ❌ | ❌ | ![PyPI - Downloads](https://img.shields.io/pypi/dm/langchain-google-bigtable?style=flat-square&label=%20) | ![PyPI - Version](https://img.shields.io/pypi/v/langchain-google-bigtable) |
    
    ## Setup
    
    ### Prerequisites
    
    To get started, you will need a Google Cloud project with an active Bigtable instance.
    * [Create a Google Cloud Project](https://developers.google.com/workspace/guides/create-project)
    * [Enable the Bigtable API](https://console.cloud.google.com/flows/enableapi?apiid=bigtable.googleapis.com)
    * [Create a Bigtable instance](https://cloud.google.com/bigtable/docs/creating-instance)
    
    ### Installation
    
    The integration is in the `langchain-google-bigtable` package. The command below also installs `langchain-google-vertexai` to use for an embedding service.
    """
    logger.info("# BigtableVectorStore")
    
    # %pip install -qU langchain-google-bigtable langchain-google-vertexai
    
    """
    **Colab only**: Uncomment the following cell to restart the kernel or use the button to restart the kernel. For Vertex AI Workbench you can restart the terminal using the button on top.
    """
    
    
    
    """
    ###  Set Your Google Cloud Project
    Set your Google Cloud project so that you can leverage Google Cloud resources within this notebook.
    
    If you don't know your project ID, try the following:
    
    * Run `gcloud config list`.
    * Run `gcloud projects list`.
    * See the support page: [Locate the project ID](https://support.google.com/googleapi/answer/7014113).
    """
    logger.info("###  Set Your Google Cloud Project")
    
    PROJECT_ID = "google.com:cloud-bigtable-dev"  # @param {type:"string"}
    INSTANCE_ID = "anweshadas-test"  # @param {type:"string"}
    TABLE_ID = "your-vector-store-table-3"  # @param {type:"string"}
    
    # !gcloud config set project {PROJECT_ID}
    
    """
    ### 🔐 Authentication
    
    Authenticate to Google Cloud as the IAM user logged into this notebook in order to access your Google Cloud Project.
    
    - If you are using Colab to run this notebook, use the cell below and continue.
    - If you are using Vertex AI Workbench, check out the setup instructions [here](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/setup-env).
    """
    logger.info("### 🔐 Authentication")
    
    
    auth.authenticate_user(project_id=PROJECT_ID)
    
    """
    ## Initialization
    
    Initializing the `BigtableVectorStore` involves three steps: setting up the embedding service, ensuring the Bigtable table is created, and configuring the store's parameters.
    
    ### 1. Set up Embedding Service
    First, we need a model to create the vector embeddings for our documents. We'll use a Vertex AI model for this example.
    """
    logger.info("## Initialization")
    
    
    embeddings = VertexAIEmbeddings(project=PROJECT_ID, model_name="gemini-embedding-001")
    
    """
    ### 2. Initialize a Table
    Before creating a `BigtableVectorStore`, a table with the correct column families must exist. The `init_vector_store_table` helper function is the recommended way to create and configure a table. If the table already exists, it will do nothing.
    """
    logger.info("### 2. Initialize a Table")
    
    
    DATA_COLUMN_FAMILY = "doc_data"
    
    try:
        init_vector_store_table(
            project_id=PROJECT_ID,
            instance_id=INSTANCE_ID,
            table_id=TABLE_ID,
            content_column_family=DATA_COLUMN_FAMILY,
            embedding_column_family=DATA_COLUMN_FAMILY,
        )
        logger.debug(f"Table '{TABLE_ID}' is ready.")
    except ValueError as e:
        logger.debug(e)
    
    """
    ### 3. Configure the Vector Store
    Now we define the parameters that control how the vector store connects to Bigtable and how it handles data.
    
    #### The BigtableEngine
    A `BigtableEngine` object manages clients and async operations. It is highly recommended to initialize a single engine and reuse it across multiple stores for better performance and resource management.
    """
    logger.info("### 3. Configure the Vector Store")
    
    
    engine = await BigtableEngine.async_initialize(project_id=PROJECT_ID)
    logger.success(format_json(engine))
    
    """
    #### Collections
    A `collection` provides a logical namespace for your documents within a single Bigtable table. It is used as a prefix for the row keys, allowing multiple vector stores to coexist in the same table without interfering with each other.
    """
    logger.info("#### Collections")
    
    collection_name = "my_docs"
    
    """
    #### Metadata Configuration
    When creating a `BigtableVectorStore`, you have two optional parameters for handling metadata:
    
    * `metadata_mappings`: This is a list of `VectorMetadataMapping` objects. You **must** define a mapping for any metadata key you wish to use for filtering in your search queries. Each mapping specifies the data type (`encoding`) for the metadata field, which is crucial for correct filtering.
    * `metadata_as_json_column`: This is an optional `ColumnConfig` that tells the store to save the *entire* metadata dictionary as a single JSON string in a specific column. This is useful for efficiently retrieving all of a document's metadata at once, including fields not defined in `metadata_mappings`. **Note:** Fields stored only in this JSON column cannot be used for filtering.
    """
    logger.info("#### Metadata Configuration")
    
    
    metadata_mappings = [
        VectorMetadataMapping(metadata_key="author", encoding=Encoding.UTF8),
        VectorMetadataMapping(metadata_key="year", encoding=Encoding.INT_BIG_ENDIAN),
        VectorMetadataMapping(metadata_key="category", encoding=Encoding.UTF8),
        VectorMetadataMapping(metadata_key="rating", encoding=Encoding.FLOAT),
    ]
    
    metadata_as_json_column = ColumnConfig(
        column_family=DATA_COLUMN_FAMILY, column_qualifier="metadata_json"
    )
    
    """
    ### 4. Create the BigtableVectorStore Instance
    """
    logger.info("### 4. Create the BigtableVectorStore Instance")
    
    content_column = ColumnConfig(
        column_family=DATA_COLUMN_FAMILY, column_qualifier="content"
    )
    embedding_column = ColumnConfig(
        column_family=DATA_COLUMN_FAMILY, column_qualifier="embedding"
    )
    
    
    vector_store = await BigtableVectorStore.create(
            project_id=PROJECT_ID,
            instance_id=INSTANCE_ID,
            table_id=TABLE_ID,
            engine=engine,
            embedding_service=embeddings,
            collection=collection_name,
            metadata_mappings=metadata_mappings,
            metadata_as_json_column=metadata_as_json_column,
            content_column=content_column,
            embedding_column=embedding_column,
        )
    logger.success(format_json(vector_store))
    
    """
    ## Manage vector store
    
    ### Add Documents
    You can add documents with pre-defined IDs. If a `Document` is added without an `id` attribute, the vector store will automatically generate a **`uuid4` string** for it.
    """
    logger.info("## Manage vector store")
    
    
    docs_to_add = [
        Document(
            page_content="A young farm boy, Luke Skywalker, is thrust into a galactic conflict.",
            id="doc_1",
            metadata={
                "author": "George Lucas",
                "year": 1977,
                "category": "sci-fi",
                "rating": 4.8,
            },
        ),
        Document(
            page_content="A hobbit named Frodo Baggins must destroy a powerful ring.",
            id="doc_2",
            metadata={
                "author": "J.R.R. Tolkien",
                "year": 1954,
                "category": "fantasy",
                "rating": 4.9,
            },
        ),
        Document(
            page_content="A group of children confront an evil entity emerging from the sewers.",
            metadata={"author": "Stephen King", "year": 1986, "category": "horror"},
        ),
        Document(
            page_content="In a distant future, the noble House Atreides rules the desert planet Arrakis.",
            id="doc_3",
            metadata={
                "author": "Frank Herbert",
                "year": 1965,
                "category": "sci-fi",
                "rating": 4.9,
            },
        ),
    ]
    
    added_ids = await vector_store.aadd_documents(docs_to_add)
    logger.success(format_json(added_ids))
    logger.debug(f"Added documents with IDs: {added_ids}")
    
    """
    ### Update Documents
    `BigtableVectorStore` handles updates by overwriting. To update a document, simply add it again with the same ID but with new content or metadata.
    """
    logger.info("### Update Documents")
    
    doc_to_update = [
        Document(
            page_content="An old hobbit, Frodo Baggins, must take a powerful ring to be destroyed.",  # Updated content
            id="doc_2",  # Same ID
            metadata={
                "author": "J.R.R. Tolkien",
                "year": 1954,
                "category": "epic-fantasy",
                "rating": 4.9,
            },  # Updated metadata
        )
    ]
    
    await vector_store.aadd_documents(doc_to_update)
    logger.debug("Document 'doc_2' has been updated.")
    
    """
    ### Delete Documents
    """
    logger.info("### Delete Documents")
    
    is_deleted = await vector_store.adelete(ids=["doc_2"])
    logger.success(format_json(is_deleted))
    
    """
    ## Query vector store
    
    ### Search
    """
    logger.info("## Query vector store")
    
    results = await vector_store.asimilarity_search("a story about a powerful ring", k=1)
    logger.success(format_json(results))
    logger.debug(results[0].page_content)
    
    """
    ### Search with Filters
    
    Apply filters before the vector search runs.
    
    #### The kNN Search Algorithm and Filtering
    
    By default, `BigtableVectorStore` uses a **k-Nearest Neighbors (kNN)** search algorithm to find the `k` vectors in the database that are most similar to your query vector. The vector store offers filtering to reduce the search space *before* the kNN search is performed, which can make queries faster and more relevant.
    
    #### Configuring Queries with `QueryParameters`
    
    All search settings are controlled via the `QueryParameters` object. This object allows you to specify not only filters but also other important search aspects:
    * `algorithm`: The search algorithm to use. Defaults to `"kNN"`.
    * `distance_strategy`: The metric used for comparison, such as `COSINE` (default) or `EUCLIDEAN`.
    * `vector_data_type`: The data type of the stored vectors, like `FLOAT32` or `DOUBLE64`. This should match the precision of your embeddings.
    * `filters`: A dictionary defining the filtering logic to apply.
    
    #### Understanding Encodings
    
    To filter on metadata fields, you must define them in `metadata_mappings` with the correct `encoding` so Bigtable can properly interpret the data. Supported encodings include:
    * **String**: `UTF8`, `UTF16`, `ASCII` for text-based metadata.
    * **Numeric**: `INT_BIG_ENDIAN` or `INT_LITTLE_ENDIAN` for integers, and `FLOAT` or `DOUBLE` for decimal numbers.
    * **Boolean**: `BOOL` for true/false values.
    
    #### Filtering Support Table
    
    | Filter Category | Key / Operator | Meaning |
    |---|---|---|
    | **Row Key** | `RowKeyFilter` | Narrows search to document IDs with a specific prefix. |
    | **Metadata Key** | `ColumnQualifiers` | Checks for the presence of one or more exact metadata keys. |
    | | `ColumnQualifierPrefix` | Checks if a metadata key starts with a given prefix. |
    | | `ColumnQualifierRegex` | Checks if a metadata key matches a regular expression. |
    | **Metadata Value** | `ColumnValueFilter` | Container for all value-based conditions. |
    | | `==` | Equality |
    | | `!=` | Inequality |
    | | `>` | Greater than |
    | | `<` | Less than |
    | | `>=` | Greater than or equal |
    | | `<=` | Less than or equal |
    | | `in` | Value is in a list. |
    | | `nin` | Value is not in a list. |
    | | `contains` | Checks for substring presence. |
    | | `like` | Performs a regex match on a string. |
    | **Logical**| `ColumnValueChainFilter` | Logical AND for combining value conditions. |
    | | `ColumnValueUnionFilter` | Logical OR for combining value conditions. |
    
    #### Complex Filter Example
    
    This example uses multiple nested logical filters. It searches for documents that are either (`category` is 'sci-fi' AND `year` between 1970-2000) OR (`author` is 'J.R.R. Tolkien') OR (`rating` > 4.5).
    """
    logger.info("### Search with Filters")
    
    
    complex_filter = {
        "ColumnValueFilter": {
            "ColumnValueUnionFilter": {  # OR
                "ColumnValueChainFilter": {  # First AND condition
                    "category": {"==": "sci-fi"},
                    "year": {">": 1970, "<": 2000},
                },
                "author": {"==": "J.R.R. Tolkien"},
            }
        }
    }
    
    query_params_complex = QueryParameters(filters=complex_filter)
    
    complex_results = await vector_store.asimilarity_search(
            "a story about a hero's journey", k=5, query_parameters=query_params_complex
        )
    logger.success(format_json(complex_results))
    
    logger.debug(f"Found {len(complex_results)} documents matching the complex filter:")
    for doc in complex_results:
        logger.debug(f"- ID: {doc.id}, Metadata: {doc.metadata}")
    
    """
    ### Search with score
    You can also retrieve the distance score along with the documents.
    """
    logger.info("### Search with score")
    
    results_with_scores = await vector_store.asimilarity_search_with_score(
            query="an evil entity", k=1
        )
    logger.success(format_json(results_with_scores))
    for doc, score in results_with_scores:
        logger.debug(f"* [SCORE={score:.4f}] {doc.page_content} [{doc.metadata}]")
    
    """
    ### Use as Retriever
    The vector store can be easily used as a retriever in RAG applications. You can specify the search type (e.g., `similarity` or `mmr`) and pass search-time arguments like `k` and `query_parameters`.
    """
    logger.info("### Use as Retriever")
    
    retriever_filter = {"ColumnValueFilter": {"category": {"==": "horror"}}}
    retriever_query_params = QueryParameters(filters=retriever_filter)
    
    retriever = vector_store.as_retriever(
        search_type="mmr",  # Specify MMR for retrieval
        search_kwargs={
            "k": 1,
            "lambda_mult": 0.8,
            "query_parameters": retriever_query_params,  # Pass filter parameters
        },
    )
    retrieved_docs = await retriever.ainvoke("a story about a hobbit")
    logger.success(format_json(retrieved_docs))
    logger.debug(retrieved_docs[0].page_content)
    
    """
    ## Usage for retrieval-augmented generation
    
    For guides on how to use this vector store for retrieval-augmented generation (RAG), see the following sections:
    
    - [Tutorials](https://python.langchain.com/docs/tutorials/rag/)
    - [How-to: Question and answer with RAG](https://python.langchain.com/docs/how_to/#qa-with-rag)
    - [Retrieval conceptual docs](https://python.langchain.com/docs/concepts/retrieval/)
    
    ## API reference
    
    For full details on the `BigtableVectorStore` class, see the source code on [GitHub](https://github.com/googleapis/langchain-google-bigtable-python/blob/main/src/langchain_google_bigtable/vector_store.py).
    """
    logger.info("## Usage for retrieval-augmented generation")
    
    logger.info("\n\n[DONE]", bright=True)

if __name__ == '__main__':
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError:
        asyncio.run(main())