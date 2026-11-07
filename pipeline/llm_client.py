import os
from openai import OpenAI

client = OpenAI(base_url="https://challengex-ext2.unissantmissionworks.com/v1", api_key=os.environ["CHALLENGEX_API_KEY"], timeout=float(os.environ.get("LLM_TIMEOUT", 40)), max_retries=0)

def backup(messages):
    """Claude, used only when the Unissant-hosted model fails and ANTHROPIC_API_KEY is set."""
    import anthropic
    r = anthropic.Anthropic(timeout=40, max_retries=0).messages.create(
        model=os.environ.get("BACKUP_MODEL", "claude-haiku-5-5"), max_tokens=2000, temperature=0,
        system="\n".join(m["content"] for m in messages if m["role"] == "system"),
        messages=[m for m in messages if m["role"] != "system"])
    return r.content[0].text

def chat(messages, **kw):
    try:
        if os.environ.get("LLM_FORCE_BACKUP"):
            raise RuntimeError("forced backup for testing")
        r = client.chat.completions.create(model="gpt-oss-20b", messages=messages, **kw)
        chat.usage = r.usage
        return r.choices[0].message.content
    except Exception:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise
        return backup(messages)
