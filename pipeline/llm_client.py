import os
from openai import OpenAI

client = OpenAI(base_url="https://challengex-ext2.unissantmissionworks.com/v1", api_key=os.environ["CHALLENGEX_API_KEY"])

def chat(messages, **kw):
    return client.chat.completions.create(model="gpt-oss-20b", messages=messages, **kw).choices[0].message.content
