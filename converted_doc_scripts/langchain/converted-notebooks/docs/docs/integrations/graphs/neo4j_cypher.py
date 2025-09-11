from jet.adapters.langchain.chat_ollama import ChatOllama
from jet.logger import logger
from langchain_core.prompts.prompt import PromptTemplate
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
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
# Neo4j

>[Neo4j](https://neo4j.com/docs/getting-started/) is a graph database management system developed by `Neo4j, Inc`.

>The data elements `Neo4j` stores are nodes, edges connecting them, and attributes of nodes and edges. Described by its developers as an ACID-compliant transactional database with native graph storage and processing, `Neo4j` is available in a non-open-source "community edition" licensed with a modification of the GNU General Public License, with online backup and high availability extensions licensed under a closed-source commercial license. Neo also licenses `Neo4j` with these extensions under closed-source commercial terms.

>This notebook shows how to use LLMs to provide a natural language interface to a graph database you can query with the `Cypher` query language.

>[Cypher](https://en.wikipedia.org/wiki/Cypher_(query_language)) is a declarative graph query language that allows for expressive and efficient data querying in a property graph.

## Setting up

You will need to have a running `Neo4j` instance. One option is to create a [free Neo4j database instance in their Aura cloud service](https://neo4j.com/cloud/platform/aura-graph-database/). You can also run the database locally using the [Neo4j Desktop application](https://neo4j.com/download/), or running a docker container.
You can run a local docker container by running the executing the following script:

```
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -d \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS=\[\"apoc\"\]  \
    neo4j:latest
```

If you are using the docker container, you need to wait a couple of second for the database to start.
"""
logger.info("# Neo4j")


graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="password")

"""
We default to Ollama models in this guide.
"""
logger.info("We default to Ollama models in this guide.")

# import getpass

# if "OPENAI_API_KEY" not in os.environ:
#     os.environ["OPENAI_API_KEY"] = getpass.getpass("Ollama API Key:")

"""
## Seeding the database

Assuming your database is empty, you can populate it using Cypher query language. The following Cypher statement is idempotent, which means the database information will be the same if you run it one or multiple times.
"""
logger.info("## Seeding the database")

graph.query(
    """
MERGE (m:Movie {name:"Top Gun", runtime: 120})
WITH m
UNWIND ["Tom Cruise", "Val Kilmer", "Anthony Edwards", "Meg Ryan"] AS actor
MERGE (a:Actor {name:actor})
MERGE (a)-[:ACTED_IN]->(m)
"""
)

"""
## Refresh graph schema information
If the schema of database changes, you can refresh the schema information needed to generate Cypher statements.
"""
logger.info("## Refresh graph schema information")

graph.refresh_schema()

logger.debug(graph.schema)

"""
## Enhanced schema information
Choosing the enhanced schema version enables the system to automatically scan for example values within the databases and calculate some distribution metrics. For example, if a node property has less than 10 distinct values, we return all possible values in the schema. Otherwise, return only a single example value per node and relationship property.
"""
logger.info("## Enhanced schema information")

enhanced_graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="password",
    enhanced_schema=True,
)
logger.debug(enhanced_graph.schema)

"""
## Querying the graph

We can now use the graph cypher QA chain to ask question of the graph
"""
logger.info("## Querying the graph")

chain = GraphCypherQAChain.from_llm(
    ChatOllama(model="llama3.2"), graph=graph, verbose=True, allow_dangerous_requests=True
)

chain.invoke({"query": "Who played in Top Gun?"})

"""
## Limit the number of results
You can limit the number of results from the Cypher QA Chain using the `top_k` parameter.
The default is 10.
"""
logger.info("## Limit the number of results")

chain = GraphCypherQAChain.from_llm(
    ChatOllama(model="llama3.2"),
    graph=graph,
    verbose=True,
    top_k=2,
    allow_dangerous_requests=True,
)

chain.invoke({"query": "Who played in Top Gun?"})

"""
## Return intermediate results
You can return intermediate steps from the Cypher QA Chain using the `return_intermediate_steps` parameter
"""
logger.info("## Return intermediate results")

chain = GraphCypherQAChain.from_llm(
    ChatOllama(model="llama3.2"),
    graph=graph,
    verbose=True,
    return_intermediate_steps=True,
    allow_dangerous_requests=True,
)

result = chain.invoke({"query": "Who played in Top Gun?"})
logger.debug(f"Intermediate steps: {result['intermediate_steps']}")
logger.debug(f"Final answer: {result['result']}")

"""
## Return direct results
You can return direct results from the Cypher QA Chain using the `return_direct` parameter
"""
logger.info("## Return direct results")

chain = GraphCypherQAChain.from_llm(
    ChatOllama(model="llama3.2"),
    graph=graph,
    verbose=True,
    return_direct=True,
    allow_dangerous_requests=True,
)

chain.invoke({"query": "Who played in Top Gun?"})

"""
## Add examples in the Cypher generation prompt
You can define the Cypher statement you want the LLM to generate for particular questions
"""
logger.info("## Add examples in the Cypher generation prompt")


CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:
MATCH (m:Movie {{name:"Top Gun"}})<-[:ACTED_IN]-()
RETURN count(*) AS numberOfActors

The question is:
{question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

chain = GraphCypherQAChain.from_llm(
    ChatOllama(model="llama3.2"),
    graph=graph,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    allow_dangerous_requests=True,
)

chain.invoke({"query": "How many people played in Top Gun?"})

"""
## Use separate LLMs for Cypher and answer generation
You can use the `cypher_llm` and `qa_llm` parameters to define different llms
"""
logger.info("## Use separate LLMs for Cypher and answer generation")

chain = GraphCypherQAChain.from_llm(
    graph=graph,
    cypher_llm=ChatOllama(model="llama3.2"),
    qa_llm=ChatOllama(model="llama3.2"),
    verbose=True,
    allow_dangerous_requests=True,
)

chain.invoke({"query": "Who played in Top Gun?"})

"""
## Ignore specified node and relationship types

You can use `include_types` or `exclude_types` to ignore parts of the graph schema when generating Cypher statements.
"""
logger.info("## Ignore specified node and relationship types")

chain = GraphCypherQAChain.from_llm(
    graph=graph,
    cypher_llm=ChatOllama(model="llama3.2"),
    qa_llm=ChatOllama(model="llama3.2"),
    verbose=True,
    exclude_types=["Movie"],
    allow_dangerous_requests=True,
)

logger.debug(chain.graph_schema)

"""
## Validate generated Cypher statements
You can use the `validate_cypher` parameter to validate and correct relationship directions in generated Cypher statements
"""
logger.info("## Validate generated Cypher statements")

chain = GraphCypherQAChain.from_llm(
    llm=ChatOllama(model="llama3.2"),
    graph=graph,
    verbose=True,
    validate_cypher=True,
    allow_dangerous_requests=True,
)

chain.invoke({"query": "Who played in Top Gun?"})

"""
## Provide context from database results as tool/function output

You can use the `use_function_response` parameter to pass context from database results to an LLM as a tool/function output. This method improves the response accuracy and relevance of an answer as the LLM follows the provided context more closely.
_You will need to use an LLM with native function calling support to use this feature_.
"""
logger.info("## Provide context from database results as tool/function output")

chain = GraphCypherQAChain.from_llm(
    llm=ChatOllama(model="llama3.2"),
    graph=graph,
    verbose=True,
    use_function_response=True,
    allow_dangerous_requests=True,
)
chain.invoke({"query": "Who played in Top Gun?"})

"""
You can provide custom system message when using the function response feature by providing `function_response_system` to instruct the model on how to generate answers.

_Note that `qa_prompt` will have no effect when using `use_function_response`_
"""
logger.info("You can provide custom system message when using the function response feature by providing `function_response_system` to instruct the model on how to generate answers.")

chain = GraphCypherQAChain.from_llm(
    llm=ChatOllama(model="llama3.2"),
    graph=graph,
    verbose=True,
    use_function_response=True,
    function_response_system="Respond as a pirate!",
    allow_dangerous_requests=True,
)
chain.invoke({"query": "Who played in Top Gun?"})

logger.info("\n\n[DONE]", bright=True)