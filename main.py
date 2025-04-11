import chainlit as cl
from datetime import datetime

from langchain_core.runnables import RunnableConfig

from agent import setup_runnable
from auth import oauth_callback, setup_memory, restore_memory

@cl.on_chat_start
async def on_chat_start():
    from chainlit import Image
    image = Image(path="opener.jpg", name="image1", display="inline")

    setup_memory()
    app_user = cl.user_session.get("user")

    # Dynamic greeting
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    await cl.Message(f"{greeting}, {app_user.identifier}!", elements=[image]).send()
    setup_runnable()

@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    restore_memory(thread)
    setup_runnable()

@cl.on_message
async def on_message(message: cl.Message):
    memory = cl.user_session.get("memory")
    runnable = cl.user_session.get("runnable")

    res = cl.Message(content="")
    async for chunk in runnable.astream(
            {"question": message.content},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()])
    ):
        await res.stream_token(chunk)

    await res.send()
    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content)
