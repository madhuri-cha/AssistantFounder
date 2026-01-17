from __future__ import print_function
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

import json
import re
import uuid
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime
from langchain_openai import ChatOpenAI
from email_server import sendEmail, EmailDraft

mcp = FastMCP(
    "Meet Schedule",
    port=8002)


model = ChatOpenAI(
        model="gpt-5.2",
        temperature=0
    )


# generate content for email scheduling


def generateContentMeeting(query:str):
    system_template = """You are an intelligent assistant that converts a user's meeting request into structured Google Calendar event data.

        generate a JSON object strictly in this format:

        {
         "summary": "<title of the meeting>",
         "description": "<short description of purpose>",
         "start": {
           "dateTime": "<ISO 8601 datetime with timezone offset, e.g. 2025-10-10T15:00:00+05:30>",
           "timeZone": "Asia/Kolkata"
         },
         "end": {
           "dateTime": "<ISO 8601 datetime with timezone offset, end time at least 30 minutes after start>",
           "timeZone": "Asia/Kolkata"
         },
         "conferenceData": {
           "createRequest": {
             
             "conferenceSolutionKey": { "type": "hangoutsMeet" }
           }
         },
         "attendees": [
           { "email": "<email1>" },
           { "email": "<email2>" }
         ]
        }

        Rules:
         Always produce valid JSON (no extra text, explanations, or markdown).
         Convert relative time expressions (e.g., "tomorrow 3 PM") into actual ISO datetimes.
         Default duration: 1 hour if not specified.
         If timezone is not mentioned, assume Asia/Kolkata.
         If description is not provided, infer it from the title.
         If no attendees are mentioned, return an empty list.
         Keep summary short (3-6 words).

    """ 

    response = model.invoke([{"role": "system", "content": system_template + f"current date and time you can refer {datetime.now()}"},{"role": "user", "content": query}])

    try:
        # Extract JSON block from response
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            
            if "conferenceData" not in data:
                data["conferenceData"] = {}
            if "createRequest" not in data["conferenceData"]:
                data["conferenceData"]["createRequest"] = {"conferenceSolutionKey": {"type": "hangoutsMeet"}}
            data["conferenceData"]["createRequest"]["requestId"] = str(uuid.uuid4())
            print("data")
            print(data)
            return data
        else:
            print("No JSON found in the response")
            return None
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Response content:", response.content)
        return None
    

SCOPES = ['https://www.googleapis.com/auth/calendar']


def create_meet_event(eventInput: dict):
    creds = None
    token_path = os.path.join(os.getcwd(), "token.json")
    credentials_path = os.path.join(os.getcwd(), "credentials.json")

    #  Load existing token if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

   
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    # Build Calendar service
    service = build('calendar', 'v3', credentials=creds)

    # Create event
    event = service.events().insert(
        calendarId='primary',
        body=eventInput,
        conferenceDataVersion=1,
    ).execute()

    meet_link = event.get("hangoutLink") or event["conferenceData"]["entryPoints"][0]["uri"]

    #  Send invitations to attendees
    for attendee in eventInput.get("attendees", []):
        sendEmail( EmailDraft(
        subject=f"Invitation: {event['summary']}",
        body=f"""Hi,

            You are invited to the following meeting:

            📅 {event['summary']}
            🕒 Starts: {event['start']['dateTime']}
            🔗 Google Meet link: {meet_link}

            See you there!
            """,
                    destination_address=attendee["email"]
                )
        )

    return {"success" : True, "message" : f"Meeting scheduled successfully: {meet_link}"}



# tool to schedule meets
@mcp.tool(name = "scheduleMeet")
def scheduleMeet(query : str):
    """
        This tool is use to schedule meets based on user query.
    """
    try:
        event = generateContentMeeting(query)
        if not event:
             return {"success":False, "message":"Failed to generate event data"}

        create_meet_event(event)
        return {"success":True, "message":"Meeting scheduled successfully!"}

    except Exception as e:
        error_msg = f"An error occurred: {e}"
        print(error_msg)
        return {"success" :False, "message" : error_msg}
    

if __name__== "__main__":
    mcp.run(
        transport="streamable-http"   
    )

