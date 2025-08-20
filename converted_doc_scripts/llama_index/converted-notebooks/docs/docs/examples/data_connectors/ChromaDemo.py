from jet.llm.mlx.adapters.mlx_llama_index_llm_adapter import MLXLlamaIndexLLMAdapter
from jet.logger import CustomLogger
from jet.models.config import MODELS_CACHE_DIR
from llama_index.core import SummaryIndex
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.chroma import ChromaReader
import logging
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
<a href="https://colab.research.google.com/github/run-llama/llama_index/blob/main/docs/docs/examples/data_connectors/ChromaDemo.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# Chroma Reader

If you're opening this Notebook on colab, you will probably need to install LlamaIndex 🦙.
"""
logger.info("# Chroma Reader")

# %pip install llama-index-readers-chroma

# !pip install llama-index


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


reader = ChromaReader(
    collection_name="chroma_collection",
    persist_directory="examples/data_connectors/chroma_collection",
)

query_vector = [n1, n2, n3, ...]

documents = reader.load_data(
    collection_name="demo", query_vector=query_vector, limit=5
)

"""
### Create index
"""
logger.info("### Create index")


index = SummaryIndex.from_documents(documents)

query_engine = index.as_query_engine()
response = query_engine.query("<query_text>")

display(Markdown(f"<b>{response}</b>"))

logger.info("\n\n[DONE]", bright=True)