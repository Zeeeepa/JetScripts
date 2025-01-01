from jet.logger import logger
from jet.llm.ollama import initialize_ollama_settings
initialize_ollama_settings()

# Using a Property Graph Store 
# 
# Normally in LlamaIndex, you'd create a `PropertyGraphStore`, pass it into a `PropertyGraphIndex`, and it would get used automatically for inserting and querying.
# 
# However, there are times when you would want to use the graph store directly. Maybe you want to create the graph yourself and hand it to a retriever or index. Maybe you want to write your own code to manage and query a graph store.
# 
# This notebook walks through populating and querying a graph store without ever using an index.

## Setup
# 
# Here, we will leverage Neo4j for our property graph store.
# 
# To launch Neo4j locally, first ensure you have docker installed. Then, you can launch the database with the following docker command
# 
# ```bash
# docker run \
#     -p 7474:7474 -p 7687:7687 \
#     -v $PWD/data:/data -v $PWD/plugins:/plugins \
#     --name neo4j-apoc \
#     -e NEO4J_apoc_export_file_enabled=true \
#     -e NEO4J_apoc_import_file_enabled=true \
#     -e NEO4J_apoc_import_file_use__neo4j__config=true \
#     -e NEO4JLABS_PLUGINS=\[\"apoc\"\] \
#     neo4j:latest
# ```
# 
# From here, you can open the db at [http://localhost:7474/](http://localhost:7474/). On this page, you will be asked to sign in. Use the default username/password of `neo4j` and `neo4j`.
# 
# Once you login for the first time, you will be asked to change the password.
# 
# After this, you are ready to create your first property graph!

from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

pg_store = Neo4jPropertyGraphStore(
    username="neo4j",
    password="llamaindex",
    url="bolt://localhost:7687",
)

## Inserting
# 
# Now that we have the store initialized, we can put some things in it!
# 
# Inserting into a property graph store consits of inserting nodes:
# - `EntityNode` - containing some labeled person, place, or thing
# - `ChunkNode` - containing some source text that an entity or relation came from
# 
# And inserting `Relation`s (i.e. linking multiple nodes).

from llama_index.core.graph_stores.types import EntityNode, ChunkNode, Relation

entity1 = EntityNode(label="PERSON", name="Logan", properties={"age": 28})
entity2 = EntityNode(label="ORGANIZATION", name="LlamaIndex")

relation = Relation(
    label="WORKS_FOR",
    source_id=entity1.id,
    target_id=entity2.id,
    properties={"since": 2023},
)

# With some entities and relations defined, we can insert them!

pg_store.upsert_nodes([entity1, entity2])
pg_store.upsert_relations([relation])

# If we wanted, we could also define a text chunk that these came from

from llama_index.core.schema import TextNode

source_node = TextNode(text="Logan (age 28), works for LlamaIndex since 2023.")
relations = [
    Relation(
        label="MENTIONS",
        target_id=entity1.id,
        source_id=source_node.node_id,
    ),
    Relation(
        label="MENTIONS",
        target_id=entity2.id,
        source_id=source_node.node_id,
    ),
]

pg_store.upsert_llama_nodes([source_node])
pg_store.upsert_relations(relations)

# Now, your graph should have 3 nodes and 3 relations.
# 
# ![low level graph](./low_level_graph.png)

## Retrieving
# 
# Now that our graph is populated with some nodes and relations, we can access some of the retrieval functions!

kg_nodes = pg_store.get(ids=[entity1.id])
print(kg_nodes)

kg_nodes = pg_store.get(properties={"age": 28})
print(kg_nodes)

paths = pg_store.get_rel_map(kg_nodes, depth=1)
for path in paths:
    print(f"{path[0].id} -> {path[1].id} -> {path[2].id}")

query = "match (n:`__Entity__`) return n"
result = pg_store.structured_query(query)
print(result)

llama_nodes = pg_store.get_llama_nodes([source_node.node_id])
print(llama_nodes[0].text)

## Upserting
# 
# You may have noticed that all the insert operations are actually upserts! As long as the ID of the node is the same, we can avoid duplicating data.
# 
# Lets update a node.

new_node = EntityNode(
    label="PERSON", name="Logan", properties={"age": 28, "location": "Canada"}
)
pg_store.upsert_nodes([new_node])

nodes = pg_store.get(properties={"age": 28})
print(nodes)

## Deleting
# 
# Deletion works similar to `get()`, with both IDs and properties.
# 
# Let's clean-up our graph for a fresh start.

pg_store.delete(ids=[entity1.id, entity2.id])

pg_store.delete([source_node.node_id])

nodes = pg_store.get(ids=[entity1.id, entity2.id])
print(nodes)

logger.info("\n\n[DONE]", bright=True)