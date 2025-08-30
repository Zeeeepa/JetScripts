async def main():
    from jet.transformers.formatters import format_json
    from IPython.display import display, Markdown
    from jet.llm.ollama.adapters.ollama_llama_index_llm_adapter import OllamaFunctionCallingAdapter
    from jet.logger import CustomLogger
    from llama_index.core import SimpleDirectoryReader
    from llama_index.core import VectorStoreIndex
    from llama_index.core.llms import LLM
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.core.query_engine import RetrieverQueryEngine
    from llama_index.core.retrievers import BaseRetriever
    from llama_index.core.schema import BaseNode, TextNode
    from llama_index.core.schema import QueryBundle, NodeWithScore
    from llama_index.core.settings import Settings
    from llama_index.core.vector_stores.simple import BasePydanticVectorStore
    from llama_index.core.vector_stores.types import VectorStoreQuery
    from llama_index.core.workflow import (
        Workflow,
        step,
        StartEvent,
        StopEvent,
        Context,
    )
    from llama_index.core.workflow import Event
    from typing import Iterable
    from typing import List, Dict, Optional, Set, FrozenSet
    import asyncio
    import os
    import shutil

    OUTPUT_DIR = os.path.join(
        os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    LOG_DIR = f"{OUTPUT_DIR}/logs"

    log_file = os.path.join(LOG_DIR, "main.log")
    logger = CustomLogger(log_file, overwrite=True)
    logger.orange(f"Logs: {log_file}")

    """
    # LongRAG Workflow
    
    This notebook shows how to implement LongRAG using LlamaIndex workflows.
    """
    logger.info("# LongRAG Workflow")

    # import nest_asyncio

    # nest_asyncio.apply()

    # %pip install -U llama-index

    # os.environ["OPENAI_API_KEY"] = "sk-proj-..."

    # !wget https://github.com/user-attachments/files/16474262/data.zip -O data.zip
    # !unzip -o data.zip
    # !rm data.zip

    """
    Since workflows are async first, this all runs fine in a notebook. If you were running in your own code, you would want to use `asyncio.run()` to start an async event loop if one isn't already running.
    
    ```python
    async def main():
        <async code>
    
    if __name__ == "__main__":
        asyncio.run(main())
    ```
    
    ## Helper Functions
    
    These helper functions will help us split documents into smaller pieces and group  nodes based on their relationships.
    """
    logger.info("## Helper Functions")

    # optionally splits documents into CHUNK_SIZE, then regroups them to demonstrate grouping algorithm
    DEFAULT_CHUNK_SIZE = 4096
    DEFAULT_MAX_GROUP_SIZE = 20  # maximum number of documents in a group
    DEFAULT_SMALL_CHUNK_SIZE = 512  # small chunk size for generating embeddings
    DEFAULT_TOP_K = 8  # top k for retrieving

    def split_doc(chunk_size: int, documents: List[BaseNode]) -> List[TextNode]:
        """Splits documents into smaller pieces.

        Args:
            chunk_size (int): Chunk size
            documents (List[BaseNode]): Documents

        Returns:
            List[TextNode]: Smaller chunks
        """
        text_parser = SentenceSplitter(chunk_size=chunk_size)
        return text_parser.get_nodes_from_documents(documents)

    def group_docs(
        nodes: List[str],
        adj: Dict[str, List[str]],
        max_group_size: Optional[int] = DEFAULT_MAX_GROUP_SIZE,
    ) -> Set[FrozenSet[str]]:
        """Groups documents.

        Args:
            nodes (List[str]): documents IDs
            adj (Dict[str, List[str]]): related documents for each document; id -> list of doc strings
            max_group_size (Optional[int], optional): max group size, None if no max group size. Defaults to DEFAULT_MAX_GROUP_SIZE.
        """
        docs = sorted(nodes, key=lambda node: len(adj[node]))
        groups = set()  # set of set of IDs
        for d in docs:
            related_groups = set()
            for r in adj[d]:
                for g in groups:
                    if r in g:
                        related_groups = related_groups.union(frozenset([g]))

            gnew = {d}
            related_groupsl = sorted(related_groups, key=lambda el: len(el))
            for g in related_groupsl:
                if max_group_size is None or len(gnew) + len(g) <= max_group_size:
                    gnew = gnew.union(g)
                    if g in groups:
                        groups.remove(g)

            groups.add(frozenset(gnew))

        return groups

    def get_grouped_docs(
        nodes: List[TextNode],
        max_group_size: Optional[int] = DEFAULT_MAX_GROUP_SIZE,
    ) -> List[TextNode]:
        """Gets list of documents that are grouped.

        Args:
            nodes (t.List[TextNode]): Input list
            max_group_size (Optional[int], optional): max group size, None if no max group size. Defaults to DEFAULT_MAX_GROUP_SIZE.

        Returns:
            t.List[TextNode]: Output list
        """
        nodes_str = [node.id_ for node in nodes]
        adj: Dict[str, List[str]] = {
            node.id_: [val.node_id for val in node.relationships.values()]
            for node in nodes
        }
        nodes_dict = {node.id_: node for node in nodes}

        res = group_docs(nodes_str, adj, max_group_size)

        ret_nodes = []
        for g in res:
            cur_node = TextNode()

            for node_id in g:
                cur_node.text += nodes_dict[node_id].text + "\n\n"
                cur_node.metadata.update(nodes_dict[node_id].metadata)

            ret_nodes.append(cur_node)

        return ret_nodes

    """
    ## Making the Retriever
    
    LongRAG needs a custom retriever, which is shown below:
    """
    logger.info("## Making the Retriever")

    class LongRAGRetriever(BaseRetriever):
        """Long RAG Retriever."""

        def __init__(
            self,
            grouped_nodes: List[TextNode],
            small_toks: List[TextNode],
            vector_store: BasePydanticVectorStore,
            similarity_top_k: int = DEFAULT_TOP_K,
        ) -> None:
            """Constructor.

            Args:
                grouped_nodes (List[TextNode]): Long retrieval units, nodes with docs grouped together based on relationships
                small_toks (List[TextNode]): Smaller tokens
                embed_model (BaseEmbedding, optional): Embed model. Defaults to None.
                similarity_top_k (int, optional): Similarity top k. Defaults to 8.
            """
            self._grouped_nodes = grouped_nodes
            self._grouped_nodes_dict = {
                node.id_: node for node in grouped_nodes}
            self._small_toks = small_toks
            self._small_toks_dict = {
                node.id_: node for node in self._small_toks}

            self._similarity_top_k = similarity_top_k
            self._vec_store = vector_store
            self._embed_model = Settings.embed_model

        def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
            """Retrieves.

            Args:
                query_bundle (QueryBundle): query bundle

            Returns:
                List[NodeWithScore]: nodes with scores
            """
            query_embedding = self._embed_model.get_query_embedding(
                query_bundle.query_str
            )
            vector_store_query = VectorStoreQuery(
                query_embedding=query_embedding, similarity_top_k=500
            )

            query_res = self._vec_store.query(vector_store_query)

            top_parents_set: Set[str] = set()
            top_parents: List[NodeWithScore] = []
            for id_, similarity in zip(query_res.ids, query_res.similarities):
                cur_node = self._small_toks_dict[id_]
                parent_id = cur_node.ref_doc_id
                if parent_id not in top_parents_set:
                    top_parents_set.add(parent_id)

                    parent_node = self._grouped_nodes_dict[parent_id]
                    node_with_score = NodeWithScore(
                        node=parent_node, score=similarity
                    )
                    top_parents.append(node_with_score)

                    if len(top_parents_set) >= self._similarity_top_k:
                        break

            assert len(top_parents) == min(
                self._similarity_top_k, len(self._grouped_nodes)
            )

            return top_parents

    """
    ## Designing the Workflow
    
    LongRAG consists of the following steps:
    
    1. Ingesting the data — grouping documents and putting them in long retrieval units, splitting the long retrieval units into smaller tokens to generate embeddings, and indexing the small nodes.
    2. Constructing the retriever and query engine.
    3. Querying over the data given a string.
    
    We define an event that passes the long and small retrieval units into the retriever and query engine.
    """
    logger.info("## Designing the Workflow")

    class LoadNodeEvent(Event):
        """Event for loading nodes."""

        small_nodes: Iterable[TextNode]
        grouped_nodes: list[TextNode]
        index: VectorStoreIndex
        similarity_top_k: int
        llm: LLM

    """
    After defining our events, we can write our workflow and steps:
    """
    logger.info(
        "After defining our events, we can write our workflow and steps:")

    class LongRAGWorkflow(Workflow):
        """Long RAG Workflow."""

        @step
        async def ingest(self, ev: StartEvent) -> LoadNodeEvent | None:
            """Ingestion step.

            Args:
                ctx (Context): Context
                ev (StartEvent): start event

            Returns:
                StopEvent | None: stop event with result
            """
            data_dir: str = ev.get("data_dir")
            llm: LLM = ev.get("llm")
            chunk_size: int | None = ev.get("chunk_size")
            similarity_top_k: int = ev.get("similarity_top_k")
            small_chunk_size: int = ev.get("small_chunk_size")
            index: VectorStoreIndex | None = ev.get("index")
            index_kwargs: dict[str, t.Any] | None = ev.get("index_kwargs")

            if any(
                i is None
                for i in [data_dir, llm, similarity_top_k, small_chunk_size]
            ):
                return None

            if not index:
                docs = SimpleDirectoryReader(data_dir).load_data()
                if chunk_size is not None:
                    nodes = split_doc(
                        chunk_size, docs
                    )  # split documents into chunks of chunk_size
                    grouped_nodes = get_grouped_docs(
                        nodes
                        # get list of nodes after grouping (groups are combined into one node), these are long retrieval units
                    )
                else:
                    grouped_nodes = docs

                small_nodes = split_doc(small_chunk_size, grouped_nodes)

                index_kwargs = index_kwargs or {}
                index = VectorStoreIndex(small_nodes, **index_kwargs)
            else:
                small_nodes = index.docstore.docs.values()
                grouped_nodes = get_grouped_docs(small_nodes, None)

            return LoadNodeEvent(
                small_nodes=small_nodes,
                grouped_nodes=grouped_nodes,
                index=index,
                similarity_top_k=similarity_top_k,
                llm=llm,
            )

        @step
        async def make_query_engine(
            self, ctx: Context, ev: LoadNodeEvent
        ) -> StopEvent:
            """Query engine construction step.

            Args:
                ctx (Context): context
                ev (LoadNodeEvent): event

            Returns:
                StopEvent: stop event
            """
            retriever = LongRAGRetriever(
                grouped_nodes=ev.grouped_nodes,
                small_toks=ev.small_nodes,
                similarity_top_k=ev.similarity_top_k,
                vector_store=ev.index.vector_store,
            )
            query_eng = RetrieverQueryEngine.from_args(retriever, ev.llm)

            return StopEvent(
                result={
                    "retriever": retriever,
                    "query_engine": query_eng,
                    "index": ev.index,
                }
            )

        @step
        async def query(self, ctx: Context, ev: StartEvent) -> StopEvent | None:
            """Query step.

            Args:
                ctx (Context): context
                ev (StartEvent): start event

            Returns:
                StopEvent | None: stop event with result
            """
            query_str: str | None = ev.get("query_str")
            query_eng = ev.get("query_eng")

            if query_str is None:
                return None

            result = query_eng.query(query_str)
            return StopEvent(result=result)

    """
    Walkthrough:
    - There are 2 entry points: one for ingesting and indexing and another for querying.
    - When ingesting, it first reads the documents, splits them into smaller nodes, and indexes them. After that, it sends a `LoadNodeEvent` which triggers the execution of `make_query_engine`, constructing a retriever and query engine from the nodes. It returns a result of the retriever, the query engine, and the index.
    - When querying, it takes in the query from the `StartEvent`, feeds it into the query engine in the context, and returns the result of the query.
    - The context is used to store the query engine.
    
    ## Running the Workflow
    """
    logger.info("## Running the Workflow")

    wf = LongRAGWorkflow(timeout=300.0)
    llm = OllamaFunctionCallingAdapter("llama3.2")
    data_dir = "/Users/jethroestrada/Desktop/External_Projects/Jet_Projects/JetScripts/data/temp/paul_graham"

    result = await wf.run(
        data_dir=data_dir,
        llm=llm,
        chunk_size=DEFAULT_CHUNK_SIZE,
        similarity_top_k=DEFAULT_TOP_K,
        small_chunk_size=DEFAULT_SMALL_CHUNK_SIZE,
    )
    logger.success(format_json(result))

    res = await wf.run(
        query_str="How can Pittsburgh become a startup hub, and what are the two types of moderates?",
        query_eng=result["query_engine"],
    )
    logger.success(format_json(res))
    display(Markdown(str(res)))

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
