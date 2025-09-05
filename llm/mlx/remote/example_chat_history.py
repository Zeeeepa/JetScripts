import os
import shutil
from jet.llm.mlx.chat_history import ChatHistory
from jet.llm.mlx.remote import generation as gen
from jet.transformers.formatters import format_json
from jet.logger import logger
from jet.file.utils import save_file

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

SYSTEM_PROMPT = """You are a helpful AI assistant engaged in a multi-turn conversation. 
Your goals:
- Be concise, clear, and friendly. 
- Remember and use details from the conversation history (e.g., user’s name). 
- Provide accurate and useful answers. 
- If the user asks personal or contextual questions, answer based on what was previously shared in this conversation. 
- Do not invent details that the user did not provide. 
- Respond in plain text without unnecessary formatting unless explicitly requested.
"""

BASE_URL = "http://localhost:8080"


def main():
    print("\n=== Chat with Conversation History ===")
    history = ChatHistory()
    response1 = gen.chat(
        "Hello, my name is Jethro Estrada",
        base_url=BASE_URL,
        with_history=True,
        history=history,
        max_tokens=50,
        verbose=True,
        system_prompt=SYSTEM_PROMPT,
    )
    logger.debug("Assistant:")
    logger.success(format_json(response1))
    save_file(response1, f"{OUTPUT_DIR}/response1.json")

    response2 = gen.chat(
        "Do you know my name?",
        base_url=BASE_URL,
        with_history=True,
        history=history,
        max_tokens=50,
        verbose=True,
        system_prompt=SYSTEM_PROMPT,
    )
    logger.success(format_json(response2))
    save_file(response2, f"{OUTPUT_DIR}/response2.json")


if __name__ == "__main__":
    main()
