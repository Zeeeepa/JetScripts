from jet.llm.mlx.adapters.mlx_llama_index_llm_adapter import MLXLlamaIndexLLMAdapter
from jet.logger import CustomLogger
from jet.models.config import MODELS_CACHE_DIR
from llama_index.core.schema import Document
from llama_index.core.schema import Document, TextNode
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.oracleai import OracleEmbeddings
from llama_index.readers.oracleai import OracleReader
from llama_index.readers.oracleai import OracleReader, OracleTextSplitter
from llama_index.readers.oracleai import OracleTextSplitter
from llama_index.utils.oracleai import OracleSummary
from llama_index.vector_stores.oracledb import OraLlamaVS, DistanceStrategy
from llama_index.vector_stores.oracledb import base as orallamavs
import oracledb
import os
import shutil
import sys


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
# Oracle AI Vector Search with Document Processing
Oracle AI Vector Search is designed for Artificial Intelligence (AI) workloads that allows you to query data based on semantics, rather than keywords.
One of the biggest benefits of Oracle AI Vector Search is that semantic search on unstructured data can be combined with relational search on business data in one single system.
This is not only powerful but also significantly more effective because you don't need to add a specialized vector database, eliminating the pain of data fragmentation between multiple systems.

In addition, your vectors can benefit from all of Oracle Database’s most powerful features, like the following:

 * [Partitioning Support](https://www.oracle.com/database/technologies/partitioning.html)
 * [Real Application Clusters scalability](https://www.oracle.com/database/real-application-clusters/)
 * [Exadata smart scans](https://www.oracle.com/database/technologies/exadata/software/smartscan/)
 * [Shard processing across geographically distributed databases](https://www.oracle.com/database/distributed-database/)
 * [Transactions](https://docs.oracle.com/en/database/oracle/oracle-database/23/cncpt/transactions.html)
 * [Parallel SQL](https://docs.oracle.com/en/database/oracle/oracle-database/21/vldbg/parallel-exec-intro.html#GUID-D28717E4-0F77-44F5-BB4E-234C31D4E4BA)
 * [Disaster recovery](https://www.oracle.com/database/data-guard/)
 * [Security](https://www.oracle.com/security/database-security/)
 * [Oracle Machine Learning](https://www.oracle.com/artificial-intelligence/database-machine-learning/)
 * [Oracle Graph Database](https://www.oracle.com/database/integrated-graph-database/)
 * [Oracle Spatial and Graph](https://www.oracle.com/database/spatial/)
 * [Oracle Blockchain](https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/dbms_blockchain_table.html#GUID-B469E277-978E-4378-A8C1-26D3FF96C9A6)
 * [JSON](https://docs.oracle.com/en/database/oracle/oracle-database/23/adjsn/json-in-oracle-database.html)

This guide demonstrates how Oracle AI Vector Search can be used with llama_index to serve an end-to-end RAG pipeline. This guide goes through examples of:

 * Loading the documents from various sources using OracleReader
 * Summarizing them within/outside the database using OracleSummary
 * Generating embeddings for them within/outside the database using OracleEmbeddings
 * Chunking them according to different requirements using Advanced Oracle Capabilities from OracleTextSplitter
 * Storing and Indexing them in a Vector Store and querying them for queries in OraLlamaVS

If you are just starting with Oracle Database, consider exploring the [free Oracle 23 AI](https://www.oracle.com/database/free/#resources) which provides a great introduction to setting up your database environment. While working with the database, it is often advisable to avoid using the system user by default; instead, you can create your own user for enhanced security and customization. For detailed steps on user creation, refer to our [end-to-end guide](https://github.com/run-llama/llama_index/blob/main/docs/docs/examples/cookbooks/oracleai_demo.ipynb) which also shows how to set up a user in Oracle. Additionally, understanding user privileges is crucial for managing database security effectively. You can learn more about this topic in the official [Oracle guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/admqs/administering-user-accounts-and-security.html#GUID-36B21D72-1BBB-46C9-A0C9-F0D2A8591B8D) on administering user accounts and security.

### Prerequisites

Please install the Oracle `llama-index` integration packages:
"""
logger.info("# Oracle AI Vector Search with Document Processing")

# %pip install llama-index
# %pip install llama_index-embeddings-oracleai
# %pip install llama_index-readers-oracleai
# %pip install llama_index-utils-oracleai
# %pip install llama-index-vector-stores-oracledb

"""
### Create Demo User
First, create a demo user with all the required privileges.
"""
logger.info("### Create Demo User")



username = "<username>"
password = "<password>"
dsn = "<hostname/service_name>"

try:
    conn = oracledb.connect(user=username, password=password, dsn=dsn)
    logger.debug("Connection successful!")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            begin
                -- Drop user
                begin
                    execute immediate 'drop user testuser cascade';
                exception
                    when others then
                        dbms_output.put_line('Error dropping user: ' || SQLERRM);
                end;

                -- Create user and grant privileges
                execute immediate 'create user testuser identified by testuser';
                execute immediate 'grant connect, unlimited tablespace, create credential, create procedure, create any index to testuser';
                execute immediate 'create or replace directory DEMO_PY_DIR as ''/scratch/hroy/view_storage/hroy_devstorage/demo/orachain''';
                execute immediate 'grant read, write on directory DEMO_PY_DIR to public';
                execute immediate 'grant create mining model to testuser';

                -- Network access
                begin
                    DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
                        host => '*',
                        ace => xs$ace_type(privilege_list => xs$name_list('connect'),
                                           principal_name => 'testuser',
                                           principal_type => xs_acl.ptype_db)
                    );
                end;
            end;
            """
        )
        logger.debug("User setup done!")
    except Exception as e:
        logger.debug(f"User setup failed with error: {e}")
    finally:
        cursor.close()
    conn.close()
except Exception as e:
    logger.debug(f"Connection failed with error: {e}")
    sys.exit(1)

"""
## Process Documents using Oracle AI
Consider the following scenario: users possess documents stored either in an Oracle Database or a file system and intend to utilize this data with Oracle AI Vector Search powered by llama_index.

To prepare the documents for analysis, a comprehensive preprocessing workflow is necessary. Initially, the documents must be retrieved, summarized (if required), and chunked as needed. Subsequent steps involve generating embeddings for these chunks and integrating them into the Oracle AI Vector Store. Users can then conduct semantic searches on this data.

The Oracle AI Vector Search llama_index library encompasses a suite of document processing tools that facilitate document loading, chunking, summary generation, and embedding creation.

In the sections that follow, we will detail the utilization of Oracle AI llama_index APIs to effectively implement each of these processes.

### Connect to Demo User
The following sample code will show how to connect to Oracle Database. By default, python-oracledb runs in a ‘Thin’ mode which connects directly to Oracle Database. This mode does not need Oracle Client libraries. However, some additional functionality is available when python-oracledb uses them. Python-oracledb is said to be in ‘Thick’ mode when Oracle Client libraries are used. Both modes have comprehensive functionality supporting the Python Database API v2.0 Specification. See the following [guide](https://python-oracledb.readthedocs.io/en/latest/user_guide/appendix_a.html#featuresummary) that talks about features supported in each mode. You might want to switch to thick-mode if you are unable to use thin-mode.
"""
logger.info("## Process Documents using Oracle AI")



username = "<username>"
password = "<password>"
dsn = "<hostname/service_name>"

try:
    conn = oracledb.connect(user=username, password=password, dsn=dsn)
    logger.debug("Connection successful!")
except Exception as e:
    logger.debug("Connection failed!")
    sys.exit(1)

"""
### Populate a Demo Table
Create a demo table and insert some sample documents.
"""
logger.info("### Populate a Demo Table")

try:
    cursor = conn.cursor()

    drop_table_sql = """drop table demo_tab"""
    cursor.execute(drop_table_sql)

    create_table_sql = """create table demo_tab (id number, data clob)"""
    cursor.execute(create_table_sql)

    insert_row_sql = """insert into demo_tab values (:1, :2)"""
    rows_to_insert = [
        (
            1,
            "If the answer to any preceding questions is yes, then the database stops the search and allocates space from the specified tablespace; otherwise, space is allocated from the database default shared temporary tablespace.",
        ),
        (
            2,
            "A tablespace can be online (accessible) or offline (not accessible) whenever the database is open.\nA tablespace is usually online so that its data is available to users. The SYSTEM tablespace and temporary tablespaces cannot be taken offline.",
        ),
        (
            3,
            "The database stores LOBs differently from other data types. Creating a LOB column implicitly creates a LOB segment and a LOB index. The tablespace containing the LOB segment and LOB index, which are always stored together, may be different from the tablespace containing the table.\nSometimes the database can store small amounts of LOB data in the table itself rather than in a separate LOB segment.",
        ),
    ]
    cursor.executemany(insert_row_sql, rows_to_insert)

    conn.commit()

    logger.debug("Table created and populated.")
    cursor.close()
except Exception as e:
    logger.debug("Table creation failed.")
    cursor.close()
    conn.close()
    sys.exit(1)

"""
With the inclusion of a demo user and a populated sample table, the remaining configuration involves setting up embedding and summary functionalities. Users are presented with multiple provider options, including local database solutions and third-party services such as Ocigenai, Hugging Face, and MLX. Should users opt for a third-party provider, they are required to establish credentials containing the necessary authentication details. Conversely, if selecting a database as the provider for embeddings, it is necessary to upload an ONNX model to the Oracle Database. No additional setup is required for summary functionalities when using the database option.

### Load ONNX Model

Oracle accommodates a variety of embedding providers, enabling users to choose between proprietary database solutions and third-party services such as OCIGENAI and HuggingFace. This selection dictates the methodology for generating and managing embeddings.

***Important*** : Should users opt for the database option, they must upload an ONNX model into the Oracle Database. Conversely, if a third-party provider is selected for embedding generation, uploading an ONNX model to Oracle Database is not required.

A significant advantage of utilizing an ONNX model directly within Oracle is the enhanced security and performance it offers by eliminating the need to transmit data to external parties. Additionally, this method avoids the latency typically associated with network or REST API calls.

Below is the example code to upload an ONNX model into Oracle Database:
"""
logger.info("### Load ONNX Model")


onnx_dir = "DEMO_PY_DIR"
onnx_file = "tinybert.onnx"
model_name = "demo_model"

try:
    OracleEmbeddings.load_onnx_model(conn, onnx_dir, onnx_file, model_name)
    logger.debug("ONNX model loaded.")
except Exception as e:
    logger.debug("ONNX model loading failed!")
    sys.exit(1)

"""
### Create Credential

When selecting third-party providers for generating embeddings, users are required to establish credentials to securely access the provider's endpoints.

***Important:*** No credentials are necessary when opting for the 'database' provider to generate embeddings. However, should users decide to utilize a third-party provider, they must create credentials specific to the chosen provider.

Below is an illustrative example:
"""
logger.info("### Create Credential")

try:
    cursor = conn.cursor()
    cursor.execute(
        """
       declare
           jo json_object_t;
       begin
           -- HuggingFace
           dbms_vector_chain.drop_credential(credential_name  => 'HF_CRED');
           jo := json_object_t();
           jo.put('access_token', '<access_token>');
           dbms_vector_chain.create_credential(
               credential_name   =>  'HF_CRED',
               params            => json(jo.to_string));

           -- OCIGENAI
           dbms_vector_chain.drop_credential(credential_name  => 'OCI_CRED');
           jo := json_object_t();
           jo.put('user_ocid','<user_ocid>');
           jo.put('tenancy_ocid','<tenancy_ocid>');
           jo.put('compartment_ocid','<compartment_ocid>');
           jo.put('private_key','<private_key>');
           jo.put('fingerprint','<fingerprint>');
           dbms_vector_chain.create_credential(
               credential_name   => 'OCI_CRED',
               params            => json(jo.to_string));
       end;
       """
    )
    cursor.close()
    logger.debug("Credentials created.")
except Exception as ex:
    cursor.close()
    raise

"""
### Load Documents
Users have the flexibility to load documents from either the Oracle Database, a file system, or both, by appropriately configuring the loader parameters. For comprehensive details on these parameters, please consult the [Oracle AI Vector Search Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/dbms_vector_chain1.html#GUID-73397E89-92FB-48ED-94BB-1AD960C4EA1F).

A significant advantage of utilizing OracleReader is its capability to process over 150 distinct file formats, eliminating the need for multiple loaders for different document types. For a complete list of the supported formats, please refer to the [Oracle Text Supported Document Formats](https://docs.oracle.com/en/database/oracle/oracle-database/23/ccref/oracle-text-supported-document-formats.html).

Below is a sample code snippet that demonstrates how to use OracleReader
"""
logger.info("### Load Documents")


loader_params = {}
loader_params = {
    "owner": "testuser",
    "tablename": "demo_tab",
    "colname": "data",
}

""" load the docs """
loader = OracleReader(conn=conn, params=loader_params)
docs = loader.load()

""" verify """
logger.debug(f"Number of docs loaded: {len(docs)}")

"""
### Generate Summary
Now that the user loaded the documents, they may want to generate a summary for each document. The Oracle AI Vector Search llama_index library offers a suite of APIs designed for document summarization. It supports multiple summarization providers such as Database, OCIGENAI, HuggingFace, among others, allowing users to select the provider that best meets their needs. To utilize these capabilities, users must configure the summary parameters as specified. For detailed information on these parameters, please consult the [Oracle AI Vector Search Guide book](https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/dbms_vector_chain1.html#GUID-EC9DDB58-6A15-4B36-BA66-ECBA20D2CE57).

***Note:*** The users may need to set proxy if they want to use some 3rd party summary generation providers other than Oracle's in-house and default provider: 'database'. If you don't have proxy, please remove the proxy parameter when you instantiate the OracleSummary.
"""
logger.info("### Generate Summary")

proxy = ""

"""
The following sample code will show how to generate summary:
"""
logger.info("The following sample code will show how to generate summary:")


summary_params = {
    "provider": "database",
    "glevel": "S",
    "numParagraphs": 1,
    "language": "english",
}

summ = OracleSummary(conn=conn, params=summary_params, proxy=proxy)

list_summary = []
for doc in docs:
    summary = summ.get_summary(doc.text)
    list_summary.append(summary)

""" verify """
logger.debug(f"Number of Summaries: {len(list_summary)}")

"""
### Split Documents
The documents may vary in size, ranging from small to very large. Users often prefer to chunk their documents into smaller sections to facilitate the generation of embeddings. A wide array of customization options is available for this splitting process. For comprehensive details regarding these parameters, please consult the [Oracle AI Vector Search Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/dbms_vector_chain1.html#GUID-4E145629-7098-4C7C-804F-FC85D1F24240).

Below is a sample code illustrating how to implement this:
"""
logger.info("### Split Documents")


splitter_params = {"normalize": "all"}

""" get the splitter instance """
splitter = OracleTextSplitter(conn=conn, params=splitter_params)

list_chunks = []
for doc in docs:
    chunks = splitter.split_text(doc.text)
    list_chunks.extend(chunks)

""" verify """
logger.debug(f"Number of Chunks: {len(list_chunks)}")

"""
### Generate Embeddings
Now that the documents are chunked as per requirements, the users may want to generate embeddings for these chunks. Oracle AI Vector Search provides multiple methods for generating embeddings, utilizing either locally hosted ONNX models or third-party APIs. For comprehensive instructions on configuring these alternatives, please refer to the [Oracle AI Vector Search Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/dbms_vector_chain1.html#GUID-C6439E94-4E86-4ECD-954E-4B73D53579DE).

***Note:*** Users may need to configure a proxy to utilize third-party embedding generation providers, excluding the 'database' provider that utilizes an ONNX model.
"""
logger.info("### Generate Embeddings")

proxy = ""

"""
The following sample code will show how to generate embeddings:
"""
logger.info("The following sample code will show how to generate embeddings:")


embedder_params = {"provider": "database", "model": "demo_model"}

embedder = OracleEmbeddings(conn=conn, params=embedder_params, proxy=proxy)

embeddings = []
for doc in docs:
    chunks = splitter.split_text(doc.text)
    for chunk in chunks:
        embed = embedder._get_text_embedding(chunk)
        embeddings.append(embed)

""" verify """
logger.debug(f"Number of embeddings: {len(embeddings)}")

"""
## Create Oracle AI Vector Store
Now that you know how to use Oracle AI llama_index library APIs individually to process the documents, let us show how to integrate with Oracle AI Vector Store to facilitate the semantic searches.

First, let's import all the dependencies.
"""
logger.info("## Create Oracle AI Vector Store")



"""
Next, let's combine all document processing stages together. Here is the sample code below:
"""
logger.info("Next, let's combine all document processing stages together. Here is the sample code below:")

"""
In this sample example, we will use 'database' provider for both summary and embeddings.
So, we don't need to do the followings:
    - set proxy for 3rd party providers
    - create credential for 3rd party providers

If you choose to use 3rd party provider,
please follow the necessary steps for proxy and credential.
"""

username = "testuser"
password = "testuser"
dsn = "<hostname/service_name>"

try:
    conn = oracledb.connect(user=username, password=password, dsn=dsn)
    logger.debug("Connection successful!")
except Exception as e:
    logger.debug("Connection failed!")
    sys.exit(1)


onnx_dir = "DEMO_PY_DIR"
onnx_file = "tinybert.onnx"
model_name = "demo_model"
try:
    OracleEmbeddings.load_onnx_model(conn, onnx_dir, onnx_file, model_name)
    logger.debug("ONNX model loaded.")
except Exception as e:
    logger.debug("ONNX model loading failed!")
    sys.exit(1)


loader_params = {
    "owner": "testuser",
    "tablename": "demo_tab",
    "colname": "data",
}
summary_params = {
    "provider": "database",
    "glevel": "S",
    "numParagraphs": 1,
    "language": "english",
}
splitter_params = {"normalize": "all"}
embedder_params = {"provider": "database", "model": "demo_model"}

loader = OracleReader(conn=conn, params=loader_params)
summary = OracleSummary(conn=conn, params=summary_params)
splitter = OracleTextSplitter(conn=conn, params=splitter_params)
embedder = OracleEmbeddings(conn=conn, params=embedder_params)

loader = OracleReader(conn=conn, params=loader_params)
docs = loader.load()

chunks_with_mdata = []
for id, doc in enumerate(docs, start=1):
    summ = summary.get_summary(doc.text)
    chunks = splitter.split_text(doc.text)
    for ic, chunk in enumerate(chunks, start=1):
        chunk_metadata = doc.metadata.copy()
        chunk_metadata["id"] = (
            chunk_metadata["_oid"] + "$" + str(id) + "$" + str(ic)
        )
        chunk_metadata["document_id"] = str(id)
        chunk_metadata["document_summary"] = str(summ[0])
        textnode = TextNode(
            text=chunk,
            id_=chunk_metadata["id"],
            embedding=embedder._get_text_embedding(chunk),
            metadata=chunk_metadata,
        )
        chunks_with_mdata.append(textnode)

""" verify """
logger.debug(f"Number of total chunks with metadata: {len(chunks_with_mdata)}")

"""
At this point, we have processed the documents and generated chunks with metadata. Next, we will create Oracle AI Vector Store with those chunks.

Here is the sample code how to do that:
"""
logger.info("At this point, we have processed the documents and generated chunks with metadata. Next, we will create Oracle AI Vector Store with those chunks.")

vectorstore = OraLlamaVS.from_documents(
    client=conn,
    docs=chunks_with_mdata,
    table_name="oravs",
    distance_strategy=DistanceStrategy.DOT_PRODUCT,
)

""" verify """
logger.debug(f"Vector Store Table: {vectorstore.table_name}")

"""
The example provided illustrates the creation of a vector store using the DOT_PRODUCT distance strategy. Users have the flexibility to employ various distance strategies with the Oracle AI Vector Store, as detailed in our [comprehensive guide](https://python.llama_index.com/v0.1/docs/integrations/vectorstores/oracle/).

With embeddings now stored in vector stores, it is advisable to establish an index to enhance semantic search performance during query execution.

***Note*** Should you encounter an "insufficient memory" error, it is recommended to increase the  ***vector_memory_size*** in your database configuration

Below is a sample code snippet for creating an index:
"""
logger.info("The example provided illustrates the creation of a vector store using the DOT_PRODUCT distance strategy. Users have the flexibility to employ various distance strategies with the Oracle AI Vector Store, as detailed in our [comprehensive guide](https://python.llama_index.com/v0.1/docs/integrations/vectorstores/oracle/).")

orallamavs.create_index(
    conn, vectorstore, params={"idx_name": "hnsw_oravs", "idx_type": "HNSW"}
)

logger.debug("Index created.")

"""
This example demonstrates the creation of a default HNSW index on embeddings within the 'oravs' table. Users may adjust various parameters according to their specific needs. For detailed information on these parameters, please consult the [Oracle AI Vector Search Guide book](https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/manage-different-categories-vector-indexes.html).

Additionally, various types of vector indices can be created to meet diverse requirements. More details can be found in our [comprehensive guide](https://github.com/run-llama/llama_index/blob/main/docs/docs/examples/vector_stores/oracle.ipynb).

## Perform Semantic Search
All set!

We have successfully processed the documents and stored them in the vector store, followed by the creation of an index to enhance query performance. We are now prepared to proceed with semantic searches.

Below is the sample code for this process:
"""
logger.info("## Perform Semantic Search")

query = "What is Oracle AI Vector Store?"
filter = {"document_id": ["1"]}

logger.debug(vectorstore.similarity_search(query, 1))

logger.debug(vectorstore.similarity_search(query, 1, filter=filter))

logger.debug(vectorstore.similarity_search_with_score(query, 1))

logger.debug(vectorstore.similarity_search_with_score(query, 1, filter=filter))

logger.debug(
    vectorstore.max_marginal_relevance_search(
        query, 1, fetch_k=20, lambda_mult=0.5
    )
)

logger.debug(
    vectorstore.max_marginal_relevance_search(
        query, 1, fetch_k=20, lambda_mult=0.5, filter=filter
    )
)

logger.info("\n\n[DONE]", bright=True)