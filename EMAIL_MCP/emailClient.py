from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

model =  ChatGoogleGenerativeAI(model="gemini-2.5-flash",api_key = api_key);
#model = ChatGroq(model="openai/gpt-oss-120b")

async def main():
    client = MultiServerMCPClient(
        {
            "Email":{
                "url":"http://localhost:8000/mcp",
                "transport" :"streamable_http"
            }
        }
    )

    tools = await client.get_tools()
    # print("Available tools ", tools)
    agent = create_react_agent(
        model, tools
    )

    email_reslopse = await agent.ainvoke(
        {"messages":[{
                "role": "system",
                "content": "You are an assistant that must always use available tools to complete tasks. For email tasks, use the sendEmail tool and do not reply without using it.The name of the sender is Prajwal"
            },
            {
                "role": "user",
                "content": "Send email to my professor about my leave for the PBL practical in next week. His email address is mohitunde7@gmail.com"
            }
            ]}
    )

asyncio.run(main())
