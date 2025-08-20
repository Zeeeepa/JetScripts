import asyncio
from jet.transformers.formatters import format_json
from jet.logger import CustomLogger
from llama_index.core.workflow import (
Workflow,
StartEvent,
StopEvent,
Context,
step,
)
from llama_index.core.workflow import Event
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel
import asyncio
import json
import os
import shutil


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
log_file = os.path.join(OUTPUT_DIR, "main.log")
logger = CustomLogger(log_file, overwrite=True)
logger.info(f"Logs: {log_file}")

"""
# Reflection Workflow for Structured Outputs

This notebook walks through setting up a `Workflow` to provide reliable structured outputs through retries and reflection on mistakes.

This notebook works best with an open-source LLM, so we will use `Ollama`. If you don't already have Ollama running, visit [https://ollama.com](https://ollama.com) to get started and download the model you want to use. (In this case, we did `ollama pull llama3.1` before running this notebook).
"""
logger.info("# Reflection Workflow for Structured Outputs")

# !pip install -U llama-index llama-index-llms-ollama

"""
Since workflows are async first, this all runs fine in a notebook. If you were running in your own code, you would want to use `asyncio.run()` to start an async event loop if one isn't already running.

```python
async def main():
    <async code>

if __name__ == "__main__":
    asyncio.run(main())
```

## Designing the Workflow

To validate the structured output of an LLM, we need only two steps:
1. Generate the structured output
2. Validate that the output is proper JSON

The key thing here is that, if the output is invalid, we **loop** until it is, giving error feedback to the next generation.

### The Workflow Events

To handle these steps, we need to define a few events:
1. An event to pass on the generated extraction 
2. An event to give feedback when the extraction is invalid

The other steps will use the built-in `StartEvent` and `StopEvent` events.
"""
logger.info("## Designing the Workflow")



class ExtractionDone(Event):
    output: str
    passage: str


class ValidationErrorEvent(Event):
    error: str
    wrong_output: str
    passage: str

"""
### Item to Extract

To prompt our model, lets define a pydantic model we want to extract.
"""
logger.info("### Item to Extract")



class Car(BaseModel):
    brand: str
    model: str
    power: int


class CarCollection(BaseModel):
    cars: list[Car]

"""
### The Workflow Itself

With our events defined, we can construct our workflow and steps. 

Note that the workflow automatically validates itself using type annotations, so the type annotations on our steps are very helpful!
"""
logger.info("### The Workflow Itself")



EXTRACTION_PROMPT = """
Context information is below:
---------------------
{passage}
---------------------

Given the context information and not prior knowledge, create a JSON object from the information in the context.
The JSON object must follow the JSON schema:
{schema}

"""

REFLECTION_PROMPT = """
You already created this output previously:
---------------------
{wrong_answer}
---------------------

This caused the JSON decode error: {error}

Try again, the response must contain only valid JSON code. Do not add any sentence before or after the JSON object.
Do not repeat the schema.
"""


class ReflectionWorkflow(Workflow):
    max_retries: int = 3

    @step
    async def extract(
        self, ctx: Context, ev: StartEvent | ValidationErrorEvent
    ) -> StopEvent | ExtractionDone:
        async def run_async_code_c80333ed():
            async def run_async_code_4b372844():
                current_retries = await ctx.store.get("retries", default=0)
                return current_retries
            current_retries = asyncio.run(run_async_code_4b372844())
            logger.success(format_json(current_retries))
            return current_retries
        current_retries = asyncio.run(run_async_code_c80333ed())
        logger.success(format_json(current_retries))
        if current_retries >= self.max_retries:
            return StopEvent(result="Max retries reached")
        else:
            async def run_async_code_a166f05d():
                await ctx.store.set("retries", current_retries + 1)
                return 
             = asyncio.run(run_async_code_a166f05d())
            logger.success(format_json())

        if isinstance(ev, StartEvent):
            passage = ev.get("passage")
            if not passage:
                return StopEvent(result="Please provide some text in input")
            reflection_prompt = ""
        elif isinstance(ev, ValidationErrorEvent):
            passage = ev.passage
            reflection_prompt = REFLECTION_PROMPT.format(
                wrong_answer=ev.wrong_output, error=ev.error
            )

        llm = Ollama(
            model="llama3",
            request_timeout=30,
            context_window=8000,
        )
        prompt = EXTRACTION_PROMPT.format(
            passage=passage, schema=CarCollection.schema_json()
        )
        if reflection_prompt:
            prompt += reflection_prompt

        async def run_async_code_6373f69d():
            async def run_async_code_712a3d81():
                output = llm.complete(prompt)
                return output
            output = asyncio.run(run_async_code_712a3d81())
            logger.success(format_json(output))
            return output
        output = asyncio.run(run_async_code_6373f69d())
        logger.success(format_json(output))

        return ExtractionDone(output=str(output), passage=passage)

    @step
    async def validate(
        self, ev: ExtractionDone
    ) -> StopEvent | ValidationErrorEvent:
        try:
            CarCollection.model_validate_json(ev.output)
        except Exception as e:
            logger.debug("Validation failed, retrying...")
            return ValidationErrorEvent(
                error=str(e), wrong_output=ev.output, passage=ev.passage
            )

        return StopEvent(result=ev.output)

"""
And thats it! Let's explore the workflow we wrote a bit.

- We have one entry point, `extract` (the steps that accept `StartEvent`)
- When `extract` finishes, it emits a `ExtractionDone` event
- `validate` runs and confirms the extraction:
  - If its ok, it emits `StopEvent` and halts the workflow
  - If nots not, it returns a `ValidationErrorEvent` with information about the error
- Any `ValidationErrorEvent` emitted will trigger the loop, and `extract` runs again!
- This continues until the structured output is validated

## Run the Workflow!

**NOTE:** With loops, we need to be mindful of runtime. Here, we set a timeout of 120s.
"""
logger.info("## Run the Workflow!")

w = ReflectionWorkflow(timeout=120, verbose=True)

async def async_func_2():
    ret = await w.run(
        passage="I own two cars: a Fiat Panda with 45Hp and a Honda Civic with 330Hp."
    )
    return ret
ret = asyncio.run(async_func_2())
logger.success(format_json(ret))

logger.debug(ret)

logger.info("\n\n[DONE]", bright=True)