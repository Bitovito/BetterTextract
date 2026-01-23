import base64
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def image_parser(filename):


  client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
  )

  # Function to encode the image
  def encode_image(image_path):
    with open(image_path, "rb") as image_file:
      return base64.b64encode(image_file.read()).decode("utf-8")


  # Path to your image
  image_path = f"./facturas/{filename}.jpeg"

  # Getting the Base64 string
  base64_image = encode_image(image_path)


  response = client.responses.create(
    model="gpt-4.1",
    input=[
        {
          "role": "user",
          "content": [
            { "type": "input_text", "text": "what's in this image?" },
            {
              "type": "input_image",
              "image_url": f"data:image/jpeg;base64,{base64_image}",
            },
        ],
      }
    ],
  )

  return response

res = image_parser("factura")
print(res.output_text)