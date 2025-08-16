from jet.logger import CustomLogger
import os
import shutil


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
log_file = os.path.join(OUTPUT_DIR, "main.log")
logger = CustomLogger(log_file, overwrite=True)
logger.info(f"Logs: {log_file}")

"""
﻿# Release Notes for AutoGen.Net v0.2.2 🚀

## Improvements 🌟
- **Update Ollama and Semantick Kernel to the latest version** : Updated Ollama and Semantick Kernel to the latest version ([#3792](https://github.com/microsoft/autogen/pull/3792)
"""
logger.info("## Improvements 🌟")

logger.info("\n\n[DONE]", bright=True)