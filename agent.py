# In agent.py
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

    # Main conversation prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "👋🏽 You are Simba, the Bano buddy. 😄\n\n"
             "Bano is a classic game played in many parts of Africa — especially Kenya — using marbles or bottle caps inside chalk circles on the ground. 🪙✨\n\n"
             "It's part strategy, part skill… and *all* fun.\n\n"
             "Respond to the user's questions in a friendly, conversational way. Use emojis occasionally to keep the conversation engaging. "
             "Address the user by their name if it's available in the context.\n\n"
             "When appropriate, use ASCII art to illustrate concepts, game setups, or fun visuals related to Bano. For example, you might draw a Bano board layout, "
             "show game pieces, or create simple decorative elements. Format the ASCII art properly by enclosing it in triple backticks to ensure correct display. "
             "Example:\n```\n    o   o\n  o       o\n   o     o\n     ooo\n```\n"
             "Only use ASCII art when it adds value to your explanation or enhances the user experience. Keep the art relatively simple and ensure it displays properly in chat."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ]
    )

    # Create the main runnable
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