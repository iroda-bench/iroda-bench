"""Reference executable for the external agent protocol."""

import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import AsyncOpenAI


async def main(prompt: str) -> str:
    config = json.loads(os.environ["IRODA_MCP_CONFIG"])
    async with (
        AsyncOpenAI(api_key="inspect-proxy", max_retries=0) as model,
        httpx.AsyncClient(headers=config.get("headers"), timeout=30) as http,
        streamable_http_client(config["url"], http_client=http) as (read, write, _),
        ClientSession(read, write) as office,
    ):
        await office.initialize()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in (await office.list_tools()).tools
        ]
        messages = [
            {
                "role": "system",
                "content": "Az IRODA eszközeivel oldd meg a feladatot. Magyarul válaszolj.",
            },
            {"role": "user", "content": prompt},
        ]
        for _ in range(20):
            response = await model.chat.completions.create(
                model=os.environ["IRODA_MODEL"],
                messages=messages,
                tools=tools,
                parallel_tool_calls=False,
            )
            message = response.choices[0].message
            if not message.tool_calls:
                return message.content or ""
            messages.append(
                message.model_dump(
                    include={"role", "content", "tool_calls"}, exclude_none=True
                )
            )
            for call in message.tool_calls:
                result = await office.call_tool(
                    call.function.name, json.loads(call.function.arguments)
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result.model_dump_json(exclude_none=True),
                    }
                )
        return ""


if __name__ == "__main__":
    print(asyncio.run(main(sys.stdin.read())))
