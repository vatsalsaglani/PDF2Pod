from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()


class OpenAIWrapper:

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def complete(self, model: str, messages: List[Dict], **kwargs):
        response = await self.client.chat.completions.create(model=model,
                                                             messages=messages,
                                                             **kwargs)
        return response

    async def function_call(self, model: str, messages: List[Dict],
                            functions: List[Dict], **kwargs):
        functions = [{
            "type": "function",
            "function": function
        } for function in functions]
        print(kwargs.get("function_call", "auto"))
        if kwargs.get("function_call", "auto") == "auto":
            choice = "auto"
        else:
            choice = {
                "type": "function",
                "function": {
                    "name": kwargs.get("function_call", "auto")
                }
            }
            del kwargs["function_call"]
        print(choice)
        if "tool_choice" in kwargs:
            del kwargs["tool_choice"]
        print(kwargs)
        response = await self.complete(model,
                                       messages,
                                       tools=functions,
                                       tool_choice=choice,
                                       **kwargs)
        response = response.choices[0].message
        print(response)
        print('\n\n\n')
        if response.tool_calls:
            return response.tool_calls[0].function
        else:
            return response.content

    async def stream(self, model: str, messages: List[Dict], **kwargs):
        response = await self.client.chat.completions.create(model=model,
                                                             messages=messages,
                                                             stream=True,
                                                             **kwargs)
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content


if __name__ == "__main__":
    import asyncio

    async def main():
        openai = OpenAIWrapper()
        # messages = [{
        #     "role": "system",
        #     "content": "You are a helpful assistant."
        # }, {
        #     "role": "user",
        #     "content": "Hello, how are you?"
        # }]
        # async for content in openai.stream("gpt-4o",
        #                                    messages,
        #                                    temperature=0.2,
        #                                    max_tokens=100):
        #     print(content, end="", flush=True)
        functions = [{
            "name": "get_weather",
            "description": "Get the weather for a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city to get the weather for"
                    }
                },
                "required": ["city"]
            }
        }]

        messages = [{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": "What is the weather in Tokyo?"
        }]
        response = await openai.function_call("gpt-4o", messages, functions)
        print(response)

    asyncio.run(main())
