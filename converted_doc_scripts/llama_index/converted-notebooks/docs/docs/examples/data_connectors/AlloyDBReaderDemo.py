import asyncio
from jet.transformers.formatters import format_json
from google.colab import auth
from jet.llm.mlx.adapters.mlx_llama_index_llm_adapter import MLXLlamaIndexLLMAdapter
from jet.logger import CustomLogger
from jet.models.config import MODELS_CACHE_DIR
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index_alloydb_pg import AlloyDBEngine
from llama_index_alloydb_pg import AlloyDBReader
import os
import shutil


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
log_file = os.path.join(OUTPUT_DIR, "main.log")
logger = CustomLogger(log_file, overwrite=True)
logger.info(f"Logs: {log_file}")

model_name = "sentence-transformers/all-MiniLM-L6-v2"
Settings.embed_model = HuggingFaceEmbedding(
    model_name=model_name,
    cache_folder=MODELS_CACHE_DIR,
)


"""
# Google AlloyDB for PostgreSQL - `AlloyDBReader`

> [AlloyDB](https://cloud.google.com/alloydb) is a fully managed relational database service that offers high performance, seamless integration, and impressive scalability. AlloyDB is 100% compatible with PostgreSQL. Extend your database application to build AI-powered experiences leveraging AlloyDB's LlamaIndex integrations.

This notebook goes over how to use `AlloyDB for PostgreSQL` to retrieve data as documents with the `AlloyDBReader` class.

Learn more about the package on [GitHub](https://github.com/googleapis/llama-index-alloydb-pg-python/).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/googleapis/llama-index-alloydb-pg-python/blob/main/samples/llama_index_reader.ipynb)

## Before you begin

To run this notebook, you will need to do the following:

 * [Create a Google Cloud Project](https://developers.google.com/workspace/guides/create-project)
 * [Enable the AlloyDB API](https://console.cloud.google.com/flows/enableapi?apiid=alloydb.googleapis.com)
 * [Create a AlloyDB cluster and instance.](https://cloud.google.com/alloydb/docs/cluster-create)
 * [Create a AlloyDB database.](https://cloud.google.com/alloydb/docs/quickstart/create-and-connect)
 * [Add a User to the database.](https://cloud.google.com/alloydb/docs/database-users/about)

### 🦙 Library Installation
Install the integration library, `llama-index-alloydb-pg`.

**Colab only:** Uncomment the following cell to restart the kernel or use the button to restart the kernel. For Vertex AI Workbench you can restart the terminal using the button on top.
"""
logger.info("# Google AlloyDB for PostgreSQL - `AlloyDBReader`")



"""
### 🔐 Authentication
Authenticate to Google Cloud as the IAM user logged into this notebook in order to access your Google Cloud Project.

* If you are using Colab to run this notebook, use the cell below and continue.
* If you are using Vertex AI Workbench, check out the setup instructions [here](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/setup-env).
"""
logger.info("### 🔐 Authentication")


auth.authenticate_user()

"""
### ☁ Set Your Google Cloud Project
Set your Google Cloud project so that you can leverage Google Cloud resources within this notebook.

If you don't know your project ID, try the following:

* Run `gcloud config list`.
* Run `gcloud projects list`.
* See the support page: [Locate the project ID](https://support.google.com/googleapi/answer/7014113).
"""
logger.info("### ☁ Set Your Google Cloud Project")

PROJECT_ID = "my-project-id"  # @param {type:"string"}

# !gcloud config set project {PROJECT_ID}

"""
## Basic Usage

### Set AlloyDB database values
Find your database values, in the [AlloyDB Instances page](https://console.cloud.google.com/alloydb/clusters).
"""
logger.info("## Basic Usage")

REGION = "us-central1"  # @param {type: "string"}
CLUSTER = "my-cluster"  # @param {type: "string"}
INSTANCE = "my-primary"  # @param {type: "string"}
DATABASE = "my-database"  # @param {type: "string"}
TABLE_NAME = "document_store"  # @param {type: "string"}
USER = "postgres"  # @param {type: "string"}
PASSWORD = "my-password"  # @param {type: "string"}

"""
### AlloyDBEngine Connection Pool

One of the requirements and arguments to establish AlloyDB Reader is a `AlloyDBEngine` object. The `AlloyDBEngine`  configures a connection pool to your AlloyDB database, enabling successful connections from your application and following industry best practices.

To create a `AlloyDBEngine` using `AlloyDBEngine.from_instance()` you need to provide only 5 things:

1. `project_id` : Project ID of the Google Cloud Project where the AlloyDB instance is located.
1. `region` : Region where the AlloyDB instance is located.
1. `cluster`: The name of the AlloyDB cluster.
1. `instance` : The name of the AlloyDB instance.
1. `database` : The name of the database to connect to on the AlloyDB instance.

By default, [IAM database authentication](https://cloud.google.com/alloydb/docs/connect-iam) will be used as the method of database authentication. This library uses the IAM principal belonging to the [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials) sourced from the environment.

Optionally, [built-in database authentication](https://cloud.google.com/alloydb/docs/database-users/about) using a username and password to access the AlloyDB database can also be used. Just provide the optional `user` and `password` arguments to `AlloyDBEngine.from_instance()`:

* `user` : Database user to use for built-in database authentication and login
* `password` : Database password to use for built-in database authentication and login.

**Note:** This tutorial demonstrates the async interface. All async methods have corresponding sync methods.
"""
logger.info("### AlloyDBEngine Connection Pool")


async def async_func_2():
    engine = await AlloyDBEngine.afrom_instance(
        project_id=PROJECT_ID,
        region=REGION,
        cluster=CLUSTER,
        instance=INSTANCE,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
    )
    return engine
engine = asyncio.run(async_func_2())
logger.success(format_json(engine))

"""
### Create AlloyDBReader

When creating an `AlloyDBReader` for fetching data from AlloyDB, you have two main options to specify the data you want to load:
* using the table_name argument - When you specify the table_name argument, you're telling the reader to fetch all the data from the given table.
* using the query argument - When you specify the query argument, you can provide a custom SQL query to fetch the data. This allows you to have full control over the SQL query, including selecting specific columns, applying filters, sorting, joining tables, etc.

### Load Documents using the `table_name` argument

#### Load Documents via default table
The reader returns a list of Documents from the table using the first column as text and all other columns as metadata. The default table will have the first column as
text and the second column as metadata (JSON). Each row becomes a document.
"""
logger.info("### Create AlloyDBReader")


async def async_func_2():
    reader = await AlloyDBReader.create(
        engine,
        table_name=TABLE_NAME,
    )
    return reader
reader = asyncio.run(async_func_2())
logger.success(format_json(reader))

"""
#### Load documents via custom table/metadata or custom page content columns
"""
logger.info("#### Load documents via custom table/metadata or custom page content columns")

async def async_func_0():
    reader = await AlloyDBReader.create(
        engine,
        table_name=TABLE_NAME,
        content_columns=["product_name"],  # Optional
        metadata_columns=["id"],  # Optional
    )
    return reader
reader = asyncio.run(async_func_0())
logger.success(format_json(reader))

"""
### Load Documents using a SQL query
The query parameter allows users to specify a custom SQL query which can include filters to load specific documents from a database.
"""
logger.info("### Load Documents using a SQL query")

table_name = "products"
content_columns = ["product_name", "description"]
metadata_columns = ["id", "content"]

reader = AlloyDBReader.create(
    engine=engine,
    query=f"SELECT * FROM {table_name};",
    content_columns=content_columns,
    metadata_columns=metadata_columns,
)

"""
**Note**: If the `content_columns` and `metadata_columns` are not specified, the reader will automatically treat the first returned column as the document’s `text` and all subsequent columns as `metadata`.

### Set page content format
The reader returns a list of Documents, with one document per row, with page content in specified string format, i.e. text (space separated concatenation), JSON, YAML, CSV, etc. JSON and YAML formats include headers, while text and CSV do not include field headers.
"""
logger.info("### Set page content format")

async def async_func_0():
    reader = await AlloyDBReader.create(
        engine,
        table_name=TABLE_NAME,
        content_columns=["product_name", "description"],
        format="YAML",
    )
    return reader
reader = asyncio.run(async_func_0())
logger.success(format_json(reader))

"""
### Load the documents

You can choose to load the documents in two ways:
* Load all the data at once
* Lazy load data

#### Load data all at once
"""
logger.info("### Load the documents")

async def run_async_code_5c1f65b4():
    async def run_async_code_52cb95b8():
        docs = await reader.aload_data()
        return docs
    docs = asyncio.run(run_async_code_52cb95b8())
    logger.success(format_json(docs))
    return docs
docs = asyncio.run(run_async_code_5c1f65b4())
logger.success(format_json(docs))

logger.debug(docs)

"""
#### Lazy Load the data
"""
logger.info("#### Lazy Load the data")

docs_iterable = reader.alazy_load_data()

docs = []
async for doc in docs_iterable:
    docs.append(doc)

logger.debug(docs)

logger.info("\n\n[DONE]", bright=True)