from datetime import datetime

import chainlit as cl
from langchain_core.runnables import RunnableConfig

from agent import setup_runnable
from auth import setup_memory, restore_memory


@cl.on_chat_start
async def on_chat_start():
    from chainlit import Image, Message

    # Dynamic greeting based on time
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # First message - greeting and introduction
    intro_text = (
        f"{greeting}! 👋🏽\n\n"
        "I'm *Simba*, your Bano buddy. I'm here to help you explore the exciting world of Bano! 🟢🎯\n"
        "Before we get started, may I know your name?"
    )

    # Send introduction without the image first
    await Message(content=intro_text).send()

    # Set flag in user session to indicate we're waiting for the name
    cl.user_session.set("waiting_for_name", True)

    # The rest of the setup will happen after we get the name
    setup_memory()
    setup_runnable()


@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    restore_memory(thread)
    setup_runnable()


@cl.on_message
async def on_message(message: cl.Message):
    # Check if we're waiting for the user's name
    waiting_for_name = cl.user_session.get("waiting_for_name", False)

    if waiting_for_name:
        # Store the user's name
        user_name = message.content
        cl.user_session.set("user_name", user_name)
        cl.user_session.set("waiting_for_name", False)

        # Load opener image now
        from chainlit import Image
        image = Image(path="opener.jpg", name="image1", display="inline")

        # Welcome message with image and personalized greeting
        welcome_text = (
            f"Nice to meet you, {user_name}! Welcome to the world of *Bano*! 🟢🎯\n\n"
            "Ready to dive into some nostalgic fun?\n"
            "You can ask me anything, or pick one of these to get started!👇"
        )
        await cl.Message(content=welcome_text, elements=[image]).send()

        # Initial suggested questions
        actions = [
            cl.Action(
                name="how_to_play",
                payload={"question": "Can you explain how to play Bano, step by step?"},
                label="How is Bano played?"
            ),
            cl.Action(
                name="bano_story",
                payload={"question": "Do you know any stories or memories people have about playing Bano?"},
                label="Tell me a Bano story"
            ),
            cl.Action(
                name="bano_history",
                payload={"question": "What's the history behind the game of Bano?"},
                label="What's the history of Bano?"
            ),
            cl.Action(
                name="where_popular",
                payload={"question": "Where is Bano mostly played, and what are the regional differences?"},
                label="Where is Bano popular?"
            ),
            cl.Action(
                name="ready_play",
                payload={"question": "I'm ready to dive in! Teach me how to play Bano like a pro."},
                label="I'm ready to play!"
            )
        ]

        await cl.Message(content="Here are some ideas you can click on:", actions=actions).send()

    else:
        # Normal message handling
        memory = cl.user_session.get("memory")
        runnable = cl.user_session.get("runnable")
        user_name = cl.user_session.get("user_name", "there")  # Default fallback

        # Add user name to the context
        context = {
            "question": message.content,
            "user_name": user_name
        }

        # Create a message for the response
        res = cl.Message(content="")

        # Stream the response
        async for chunk in runnable.astream(
                context,
                config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()])
        ):
            await res.stream_token(chunk)

        await res.send()

        # Generate contextual follow-up suggestions based on the topic
        # This is a more reliable approach than trying to generate them with the LLM
        topic = message.content.lower()

        # Determine appropriate follow-up questions based on the conversation context
        if "play" in topic or "rules" in topic or "how to" in topic:
            follow_ups = [
                {"question": "What are some winning strategies for Bano?", "label": "Winning strategies?"},
                {"question": "Are there different variations of Bano?", "label": "Game variations"},
                {"question": "What equipment do I need to play Bano?", "label": "Equipment needed"}
            ]
        elif "history" in topic or "origin" in topic:
            follow_ups = [
                {"question": "What cultural significance does Bano have?", "label": "Cultural significance"},
                {"question": "Are there similar games in other cultures?", "label": "Similar games"},
                {"question": "How has Bano evolved over time?", "label": "Evolution of Bano"}
            ]
        elif "region" in topic or "country" in topic or "where" in topic or "location" in topic:
            follow_ups = [
                {"question": "How is Bano played specifically in Kenya?", "label": "Kenyan style"},
                {"question": "How does Bano differ in Tanzania?", "label": "Tanzanian variations"},
                {"question": "Has Bano spread beyond East Africa?", "label": "Global reach"}
            ]
        elif "story" in topic or "memory" in topic or "experience" in topic:
            follow_ups = [
                {"question": "Are there any famous Bano players?", "label": "Famous players"},
                {"question": "Are there Bano tournaments or competitions?", "label": "Tournaments"},
                {"question": "Can you share a story about a memorable Bano game?", "label": "Memorable games"}
            ]
        else:
            # Default follow-ups for general questions
            follow_ups = [
                {"question": "Can you explain the basic rules of Bano?", "label": "Basic rules"},
                {"question": "Why is Bano so popular in East Africa?", "label": "Popularity reasons"},
                {"question": "How can I learn to play Bano well?", "label": "Learning tips"}
            ]

        # Create action buttons with the simplified approach
        actions = [
            cl.Action(
                name="dynamic_suggestion",
                payload={"question": item["question"]},
                label=item["label"]
            )
            for item in follow_ups
        ]

        # Send follow-up suggestions as a separate message
        await cl.Message(content="Would you like to know more about:", actions=actions).send()

        # Update memory
        memory.chat_memory.add_user_message(message.content)
        memory.chat_memory.add_ai_message(res.content)


# Static action callbacks for initial buttons
@cl.action_callback("how_to_play")
async def on_how_to_play_action(action):
    question = "Can you explain how to play Bano, step by step?"
    await on_message(cl.Message(content=question))


@cl.action_callback("bano_story")
async def on_bano_story_action(action):
    question = "Do you know any stories or memories people have about playing Bano?"
    await on_message(cl.Message(content=question))


@cl.action_callback("bano_history")
async def on_bano_history_action(action):
    question = "What's the history behind the game of Bano?"
    await on_message(cl.Message(content=question))


@cl.action_callback("where_popular")
async def on_where_popular_action(action):
    question = "Where is Bano mostly played, and what are the regional differences?"
    await on_message(cl.Message(content=question))


@cl.action_callback("ready_play")
async def on_ready_play_action(action):
    question = "I'm ready to dive in! Teach me how to play Bano like a pro."
    await on_message(cl.Message(content=question))


# Generic callback for dynamic suggestion buttons
@cl.action_callback("dynamic_suggestion")
async def on_dynamic_suggestion_action(action):
    question = action.payload.get("question", "")
    if question:
        await on_message(cl.Message(content=question))