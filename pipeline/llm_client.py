import os
from openai import OpenAI

client = OpenAI(base_url="https://challengex-ext2.unissantmissionworks.com/v1", api_key=os.environ["CHALLENGEX_API_KEY"], timeout=float(os.environ.get("LLM_TIMEOUT", 40)), max_retries=0)

def chat(messages, **kw):
    r = client.chat.completions.create(model="gpt-oss-20b", messages=messages, **kw)
    chat.usage = r.usage
    return r.choices[0].message.content
