
from httpx import Client
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
model = ChatGroq(model="openai/gpt-oss-120b")



async def main():
    client = MultiServerMCPClient(
        {
            "math":{
                "command":"python",
                "args":["V1_MCP\mathserver.py"],
                "transport":"stdio",
            },

            "weather":{
                "url":"http://localhost:8000/mcp",
                "transport" :"streamable_http"
            }
        }
    )


    tools = await client.get_tools()
    
    agent = create_react_agent(
       model, tools
    )

    math_response = await agent.ainvoke(
        {"messages":[{"role":"user", "content":"What's (3+5)x 12?"}]}
    )

    print("Math response : ", math_response["messages"][-1].content)

    weather_response = await agent.ainvoke(
        {"messages":[{"role":"user", "content":"What is the weather in India"}]}
    )

    print("Weather response : ", weather_response["messages"][-1].content)


asyncio.run(main())