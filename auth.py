from typing import Dict, Optional
from chainlit.types import ThreadDict
import chainlit as cl
from langchain.memory import ConversationBufferMemory

@cl.oauth_callback
def oauth_callback(provider_id: str, token: str, raw_user_data: Dict[str, str], default_user: cl.User) -> Optional[cl.User]:
    return default_user

def setup_memory():
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))

def restore_memory(thread: ThreadDict):
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [m for m in thread["steps"] if m["parentId"] is None]
    for message in root_messages:
        if message["type"] == "user_message":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])
    cl.user_session.set("memory", memory)
