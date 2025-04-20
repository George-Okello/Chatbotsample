from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.utilities import SerpAPIWrapper
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool

from chainlit import user_session

# Setup Search Tool
search = SerpAPIWrapper(serpapi_api_key="your_serpapi_key")

search_tool = Tool(
    name="Search",
    func=search.run,
    description="Use this tool when you need to search for real-world facts or updates."
)

def setup_runnable() -> Runnable:
    memory = user_session.get("memory")  # type: ConversationBufferMemory
    model = ChatCohere(streaming=True)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Hey there! I'm Simba. Great to have you here! 😊\n\n"
                "Ever played 'Bano'? It's a classic Kenyan marble game—super fun! 🎯\n\n"
                "Before we dive in, what's your name? And how’s your day going?\n\n"
                "(Take your time. Just say 'ready' when you want to start.)"
            ),
            ("placeholder", "history"),
            ("human", "{question}")
        ]
    )

    runnable = (
            RunnablePassthrough.assign(
                history=RunnableLambda(lambda _: [
                    msg for msg in memory.load_memory_variables({}).get("history", [])
                    if msg and getattr(msg, "content", None)
                ])
            )
            | prompt
            | model
            | StrOutputParser()
    )

    user_session.set("runnable", runnable)
    return runnable
