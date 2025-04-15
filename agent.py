import os
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_community.utilities import SerpAPIWrapper
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool

from chainlit import user_session

load_dotenv()
search = SerpAPIWrapper(serpapi_api_key=os.getenv("SERPAPI_API_KEY"))

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
            ("system",
             "👋🏽 Hey there! I’m *Simba*, your Bano buddy. 😄\n\n"
             "Before we dive into marbles and memories — what’s your name? And how’s your day going so far? 🤗\n\n"
             "So… have you ever heard of **Bano**? 🟢🎯 It’s a classic game played in many parts of Africa — especially Kenya — "
             "using marbles or bottle caps inside chalk circles on the ground. 🪙✨\n\n"
             "It’s part strategy, part skill… and *all* fun. Whether you played it, saw it, or this is your first time hearing about it — "
             "you’re in the right place. 😎\n\n"
             "Here’s a quick sketch of how it might look:\n\n"
             "    ________     \n"
             "   /  o o  \\    \n"
             "  / o     o \\   <- Chalk circle\n"
             " |  o     o  |  <- Marbles inside\n"
             "  \\   o o   /   \n"
             "   \\______/    \n\n"
             "Just type *'ready'* when you're good to dive into the world of Bano! 💬🔥"
            ),
            MessagesPlaceholder(variable_name="history"),
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
