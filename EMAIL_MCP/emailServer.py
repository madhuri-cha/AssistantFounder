from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import smtplib
from email.message import EmailMessage
import json

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

mcp = FastMCP("Email")

model =  ChatGoogleGenerativeAI(model="gemini-2.5-flash",api_key = api_key);


from pydantic import BaseModel

class SendEmailArgs(BaseModel):
    to: str
    subject: str
    body: str

class SendEmailResponse(BaseModel):
    success: bool
    message: str

def generateContent(query:str):
    template = """You are the exper email generator. You have provided with the user response.
        Your task is to compose email regarding that response.
        
        user query:
        {query}

        From the above user query, you have to generate the subject and body of the email. 

        Output format you have to follow:
        {
            subject : "",
            body : "",
            destination_address : "",
        }

        Note that user will provide you the destination email address which you have to identify and add into the above output.

        Make sure that you strictly follow the above output format and doen't give anything else as I have to use this in further code.            
    """

    prompt = PromptTemplate(
        input_variables=["query"],
        template=template
    )

    final_prompt = prompt.format(query = query);

    response = model.invoke({"contents": [{"role": "user", "content": final_prompt}]})
    print(response)
    try:
        data = json.loads(response.content)
        return data
    except json.JSONDecodeError as e:
        print("Failed to parse LLM output:", e)
        raise

    return response


def send_email(data:dict):
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
def sendEmail(args: SendEmailArgs) -> bool:
    print("sendEmail tool triggered with:", args)
    from_email = os.getenv('APP_EMAIL')
    from_password = os.getenv('APP_PASSCODE')

    msg = EmailMessage()
    msg['Subject'] = args.subject
    msg['From'] = from_email
    msg['To'] = args.to
    msg.set_content(args.body)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(from_email, from_password)
            smtp.send_message(msg)
            print("Email sent successfully!")
            return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False



if __name__== "__main__":
    print("Starting MCP server with tools:")
    mcp.run(transport="streamable-http")






