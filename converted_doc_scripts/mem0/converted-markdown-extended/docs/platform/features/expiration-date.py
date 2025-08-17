from jet.logger import CustomLogger
from mem0 import MemoryClient
import MemoryClient from 'mem0ai'
import datetime
import os
import shutil


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "generated", os.path.splitext(os.path.basename(__file__))[0])
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
log_file = os.path.join(OUTPUT_DIR, "main.log")
logger = CustomLogger(log_file, overwrite=True)
logger.info(f"Logs: {log_file}")

"""
---
title: Expiration Date
description: 'Set time-bound memories in Mem0 with automatic expiration dates to manage temporal information effectively.'
icon: "clock"
iconType: "solid"
---

## Benefits of Memory Expiration

Setting expiration dates for memories offers several advantages:

• **Time-Sensitive Information Management**: Handle information that's only relevant for a specific time period.

• **Event-Based Memory**: Manage information related to upcoming events that becomes irrelevant after the event passes.

These benefits enable more sophisticated memory management for applications where temporal context matters.

## Setting Memory Expiration Date

You can set an expiration date for memories, after which they will no longer be retrieved in searches. This is useful for creating temporary memories or memories that are only relevant for a specific time period.

<CodeGroup>
"""
logger.info("## Benefits of Memory Expiration")


client = MemoryClient(api_key="your-api-key")

messages = [
    {
        "role": "user",
        "content": "I'll be in San Francisco until end of this month."
    }
]

client.add(messages=messages, user_id="alex", expiration_date=str(datetime.datetime.now().date() + datetime.timedelta(days=30)))

client.add(messages=messages, user_id="alex", expiration_date="2023-08-31")

"""

"""

client = new MemoryClient({ apiKey: 'your-api-key' })

messages = [
    {
        "role": "user",
        "content": "I'll be in San Francisco until end of this month."
    }
]

expirationDate = new Date()
expirationDate.setDate(expirationDate.getDate() + 30)
client.add(messages, {
    user_id: "alex",
    expiration_date: expirationDate.toISOString().split('T')[0]
})
    .then(response => console.log(response))
    .catch(error => console.error(error))

client.add(messages, {
    user_id: "alex",
    expiration_date: "2023-08-31"
})
    .then(response => console.log(response))
    .catch(error => console.error(error))

"""

"""

curl -X POST "https://api.mem0.ai/v1/memories/" \
     -H "Authorization: Token your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
         "messages": [
             {
                "role": "user",
                "content": "I'll be in San Francisco until end of this month."
            }
         ],
         "user_id": "alex",
         "expiration_date": "2023-08-31"
     }'

"""

"""

{
    "results": [
        {
            "id": "a1b2c3d4-e5f6-4g7h-8i9j-k0l1m2n3o4p5",
            "data": {
                "memory": "In San Francisco until end of this month"
            },
            "event": "ADD"
        }
    ]
}

"""
</CodeGroup>

<Note>
Once a memory reaches its expiration date, it won't be included in search or get results, though the data remains stored in the system.
</Note>

If you have any questions, please feel free to reach out to us using one of the following methods:

<Snippet file="get-help.mdx" />
"""
logger.info("Once a memory reaches its expiration date, it won't be included in search or get results, though the data remains stored in the system.")

logger.info("\n\n[DONE]", bright=True)