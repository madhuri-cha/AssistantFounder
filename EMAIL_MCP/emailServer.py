from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import smtplib
from email.message import EmailMessage
import json
from langchain_ollama import ChatOllama 
import re


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

mcp = FastMCP("Email")

# model =  ChatGoogleGenerativeAI(model="gemini-2.5-flash",api_key = api_key);
model = ChatOllama(model="llama3")

from pydantic import BaseModel

class SendEmailArgs(BaseModel):
    user_query : str


class SendEmailResponse(BaseModel):
    success: bool
    message: str


def generateContent(query:str):
    template = """You are an expert email generator. You are provided with the user's query.
    Your task is to compose an email based on that query.

    User query:
    {query}

    Generate the subject, body, and destination address in the following JSON format. The output must be a valid JSON object with double quotes around keys and string values. Escape newline characters, carriage returns, and other special characters properly using backslashes.

    Respond ONLY with the JSON object. Do not include any explanation, text, or other formatting.

    If you are unable to generate a valid email, respond with:
    {{
        "subject": "",
        "body": "",
        "destination_address": ""
    }}

    
    """
    prompt = PromptTemplate(
        input_variables=["query"],
        template=template
    )
    final_prompt = prompt.format(query = query)

    response = model.invoke([{"role": "system", "content": "Compose mail alinghed with subject and destination address should be accurate."},{"role": "user", "content": final_prompt}])
    print("Raw response:", response.content)

    

    try:
        # Extract JSON block from response
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            return data
        else:
            print("No JSON found in the response")
            return None
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Response content:", response.content)
        return None
    



def send_email(data:dict):
    print(data)
    from_email = os.getenv('APP_EMAIL')
    from_password = os.getenv('APP_PASSCODE')

    msg = EmailMessage()
    msg['Subject'] = data["subject"]
    msg['From'] = from_email
    msg['To'] = data["destination_address"]
    msg.set_content(data["body"])

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(from_email, from_password)
            smtp.send_message(msg)
            return SendEmailResponse(success=True, message="Email sent successfully!")
    except Exception as e:
        error_msg = f"An error occurred: {e}"
        print(error_msg)
        return SendEmailResponse(success=False, message=error_msg)



@mcp.tool()
def sendEmail(args: SendEmailArgs) -> SendEmailResponse:
    """
    This tool will be used for sending the email.
    """

    try:
       email_body = generateContent(args.user_query)
       print(email_body)
       return send_email(email_body)

    except Exception as e:
        error_msg = f"An error occurred: {e}"
        print(error_msg)
        return SendEmailResponse(success=False, message=error_msg)



if __name__== "__main__":
    print("Starting MCP server with tools:")
    mcp.run(transport="streamable-http")






