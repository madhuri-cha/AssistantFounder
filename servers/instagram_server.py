import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
import requests
import os
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

    
mcp = FastMCP("Instagram", port=8000)

load_dotenv()

long_lived_token = os.getenv("long_lived_token")
ig_user_id = os.getenv("ig_user_id")

client = OpenAI()





@mcp.tool(name = "createImage")
def createImage(user_instrucion:str):
    """ This tool creates an image using DALL·E """
    result = client.images.generate(
            model="dall-e-3",
            prompt=user_instrucion,
            size="1024x1024"
        )

    image_url = result.data[0].url
    if not image_url:
        return {
                "success" : False,
                "message" :"Image generation failed"
            }
    return image_url
    
@mcp.tool(name = "postImage")
def post_image(image_url):
    """
    This tool posts image on instagram based on it's link to Instagram.
    """
    try:       

        # 2️ Create media container
        media_url = f"https://graph.facebook.com/v17.0/{ig_user_id}/media"

        payload = {
            "image_url": image_url,
            "caption": "Sample content",
            "access_token": long_lived_token
        }

        response = requests.post(media_url, params=payload)
        data = response.json()

        if "id" not in data:
            return {
                "success" : False,
                "message" : f"Failed to create media container: {data}"
            }

        creation_id = data["id"]

        # 3️ Publish media
        publish_url = f"https://graph.facebook.com/v17.0/{ig_user_id}/media_publish"

        publish_payload = {
            "creation_id": creation_id,
            "access_token": long_lived_token
        }

        publish_response = requests.post(publish_url, params=publish_payload)
        publish_data = publish_response.json()

        if "id" not in publish_data:
            return {
                "success" : False,
                "message" : f"Failed to publish media: {publish_data}"
            }

        #  Success
        return {
            "success" : True,
            "message" : "Image successfully posted to Instagram"
        }

    except Exception as e:
        return {
            "success" : False,
            "message" : f"Unexpected error: {str(e)}"
        }

    

if __name__== "__main__":
    print("Starting MCP server with tools:")
    mcp.run(transport="streamable-http")