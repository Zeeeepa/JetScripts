from google.auth import compute_engine
from google.cloud import firestore
from google.colab import auth
from jet.logger import logger
from langchain_google_firestore import FirestoreChatMessageHistory
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
# Google Firestore (Native Mode)

> [Google Cloud Firestore](https://cloud.google.com/firestore) is a serverless document-oriented database that scales to meet any demand. Extend your database application to build AI-powered experiences leveraging `Firestore's` Langchain integrations.

This notebook goes over how to use [Google Cloud Firestore](https://cloud.google.com/firestore) to store chat message history with the `FirestoreChatMessageHistory` class.

Learn more about the package on [GitHub](https://github.com/googleapis/langchain-google-firestore-python/).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/googleapis/langchain-google-firestore-python/blob/main/docs/chat_message_history.ipynb)

## Before You Begin

To run this notebook, you will need to do the following:

* [Create a Google Cloud Project](https://developers.google.com/workspace/guides/create-project)
* [Enable the Firestore API](https://console.cloud.google.com/flows/enableapi?apiid=firestore.googleapis.com)
* [Create a Firestore database](https://cloud.google.com/firestore/docs/manage-databases)

After confirmed access to database in the runtime environment of this notebook, filling the following values and run the cell before running example scripts.

### 🦜🔗 Library Installation

The integration lives in its own `langchain-google-firestore` package, so we need to install it.
"""
logger.info("# Google Firestore (Native Mode)")

# %pip install --upgrade --quiet langchain-google-firestore

"""
**Colab only**: Uncomment the following cell to restart the kernel or use the button to restart the kernel. For Vertex AI Workbench you can restart the terminal using the button on top.
"""



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
### 🔐 Authentication

Authenticate to Google Cloud as the IAM user logged into this notebook in order to access your Google Cloud Project.

- If you are using Colab to run this notebook, use the cell below and continue.
- If you are using Vertex AI Workbench, check out the setup instructions [here](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/setup-env).
"""
logger.info("### 🔐 Authentication")


auth.authenticate_user()

"""
## Basic Usage

### FirestoreChatMessageHistory

To initialize the `FirestoreChatMessageHistory` class you need to provide only 3 things:

1. `session_id` - A unique identifier string that specifies an id for the session.
1. `collection` : The single `/`-delimited path to a Firestore collection.
"""
logger.info("## Basic Usage")


chat_history = FirestoreChatMessageHistory(
    session_id="user-session-id", collection="HistoryMessages"
)

chat_history.add_user_message("Hi!")
chat_history.add_ai_message("How can I help you?")

chat_history.messages

"""
#### Cleaning up
When the history of a specific session is obsolete and can be deleted from the database and memory, it can be done the following way.

**Note:** Once deleted, the data is no longer stored in Firestore and is gone forever.
"""
logger.info("#### Cleaning up")

chat_history.clear()

"""
### Custom Client

The client is created by default using the available environment variables. A [custom client](https://cloud.google.com/python/docs/reference/firestore/latest/client) can be passed to the constructor.
"""
logger.info("### Custom Client")


client = firestore.Client(
    project="project-custom",
    database="non-default-database",
    credentials=compute_engine.Credentials(),
)

history = FirestoreChatMessageHistory(
    session_id="session-id", collection="History", client=client
)

history.add_user_message("New message")

history.messages

history.clear()

logger.info("\n\n[DONE]", bright=True)