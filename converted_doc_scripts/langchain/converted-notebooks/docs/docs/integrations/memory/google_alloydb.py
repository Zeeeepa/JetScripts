from google.colab import auth
from jet.logger import logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_alloydb_pg import AlloyDBChatMessageHistory
from langchain_google_alloydb_pg import AlloyDBEngine
from langchain_google_vertexai import ChatVertexAI
import os
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
# Google AlloyDB for PostgreSQL

> [Google Cloud AlloyDB for PostgreSQL](https://cloud.google.com/alloydb) is a fully managed `PostgreSQL` compatible database service for your most demanding enterprise workloads. `AlloyDB` combines the best of `Google Cloud` with `PostgreSQL`, for superior performance, scale, and availability. Extend your database application to build AI-powered experiences leveraging `AlloyDB` Langchain integrations.

This notebook goes over how to use `Google Cloud AlloyDB for PostgreSQL` to store chat message history with the `AlloyDBChatMessageHistory` class.

Learn more about the package on [GitHub](https://github.com/googleapis/langchain-google-alloydb-pg-python/).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/googleapis/langchain-google-alloydb-pg-python/blob/main/docs/chat_message_history.ipynb)

## Before You Begin

To run this notebook, you will need to do the following:

 * [Create a Google Cloud Project](https://developers.google.com/workspace/guides/create-project)
 * [Enable the AlloyDB API](https://console.cloud.google.com/flows/enableapi?apiid=alloydb.googleapis.com)
 * [Create a AlloyDB instance](https://cloud.google.com/alloydb/docs/instance-primary-create)
 * [Create a AlloyDB database](https://cloud.google.com/alloydb/docs/database-create)
 * [Add an IAM database user to the database](https://cloud.google.com/alloydb/docs/manage-iam-authn) (Optional)

### 🦜🔗 Library Installation
The integration lives in its own `langchain-google-alloydb-pg` package, so we need to install it.
"""
logger.info("# Google AlloyDB for PostgreSQL")

# %pip install --upgrade --quiet langchain-google-alloydb-pg langchain-google-vertexai

"""
**Colab only:** Uncomment the following cell to restart the kernel or use the button to restart the kernel. For Vertex AI Workbench you can restart the terminal using the button on top.
"""



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
### 💡 API Enablement
The `langchain-google-alloydb-pg` package requires that you [enable the AlloyDB Admin API](https://console.cloud.google.com/flows/enableapi?apiid=alloydb.googleapis.com) in your Google Cloud Project.
"""
logger.info("### 💡 API Enablement")

# !gcloud services enable alloydb.googleapis.com

"""
## Basic Usage

### Set AlloyDB database values
Find your database values, in the [AlloyDB cluster page](https://console.cloud.google.com/alloydb?_ga=2.223735448.2062268965.1707700487-2088871159.1707257687).
"""
logger.info("## Basic Usage")

REGION = "us-central1"  # @param {type: "string"}
CLUSTER = "my-alloydb-cluster"  # @param {type: "string"}
INSTANCE = "my-alloydb-instance"  # @param {type: "string"}
DATABASE = "my-database"  # @param {type: "string"}
TABLE_NAME = "message_store"  # @param {type: "string"}

"""
### AlloyDBEngine Connection Pool

One of the requirements and arguments to establish AlloyDB as a ChatMessageHistory memory store is a `AlloyDBEngine` object. The `AlloyDBEngine`  configures a connection pool to your AlloyDB database, enabling successful connections from your application and following industry best practices.

To create a `AlloyDBEngine` using `AlloyDBEngine.from_instance()` you need to provide only 5 things:

1. `project_id` : Project ID of the Google Cloud Project where the AlloyDB instance is located.
1. `region` : Region where the AlloyDB instance is located.
1. `cluster`: The name of the AlloyDB cluster.
1. `instance` : The name of the AlloyDB instance.
1. `database` : The name of the database to connect to on the AlloyDB instance.

By default, [IAM database authentication](https://cloud.google.com/alloydb/docs/manage-iam-authn) will be used as the method of database authentication. This library uses the IAM principal belonging to the [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials) sourced from the envionment.

Optionally, [built-in database authentication](https://cloud.google.com/alloydb/docs/database-users/about) using a username and password to access the AlloyDB database can also be used. Just provide the optional `user` and `password` arguments to `AlloyDBEngine.from_instance()`:

* `user` : Database user to use for built-in database authentication and login
* `password` : Database password to use for built-in database authentication and login.
"""
logger.info("### AlloyDBEngine Connection Pool")


engine = AlloyDBEngine.from_instance(
    project_id=PROJECT_ID,
    region=REGION,
    cluster=CLUSTER,
    instance=INSTANCE,
    database=DATABASE,
)

"""
### Initialize a table
The `AlloyDBChatMessageHistory` class requires a database table with a specific schema in order to store the chat message history.

The `AlloyDBEngine` engine has a helper method `init_chat_history_table()` that can be used to create a table with the proper schema for you.
"""
logger.info("### Initialize a table")

engine.init_chat_history_table(table_name=TABLE_NAME)

"""
### AlloyDBChatMessageHistory

To initialize the `AlloyDBChatMessageHistory` class you need to provide only 3 things:

1. `engine` - An instance of a `AlloyDBEngine` engine.
1. `session_id` - A unique identifier string that specifies an id for the session.
1. `table_name` : The name of the table within the AlloyDB database to store the chat message history.
"""
logger.info("### AlloyDBChatMessageHistory")


history = AlloyDBChatMessageHistory.create_sync(
    engine, session_id="test_session", table_name=TABLE_NAME
)
history.add_user_message("hi!")
history.add_ai_message("whats up?")

history.messages

"""
#### Cleaning up
When the history of a specific session is obsolete and can be deleted, it can be done the following way.

**Note:** Once deleted, the data is no longer stored in AlloyDB and is gone forever.
"""
logger.info("#### Cleaning up")

history.clear()

"""
## 🔗 Chaining

We can easily combine this message history class with [LCEL Runnables](/docs/how_to/message_history)

To do this we will use one of [Google's Vertex AI chat models](/docs/integrations/chat/google_vertex_ai_palm) which requires that you [enable the Vertex AI API](https://console.cloud.google.com/flows/enableapi?apiid=aiplatform.googleapis.com) in your Google Cloud Project.
"""
logger.info("## 🔗 Chaining")

# !gcloud services enable aiplatform.googleapis.com


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

chain = prompt | ChatVertexAI(project=PROJECT_ID)

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: AlloyDBChatMessageHistory.create_sync(
        engine,
        session_id=session_id,
        table_name=TABLE_NAME,
    ),
    input_messages_key="question",
    history_messages_key="history",
)

config = {"configurable": {"session_id": "test_session"}}

chain_with_history.invoke({"question": "Hi! I'm bob"}, config=config)

chain_with_history.invoke({"question": "Whats my name"}, config=config)

logger.info("\n\n[DONE]", bright=True)