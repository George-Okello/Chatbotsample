from datetime import datetime

import chainlit as cl
from langchain_core.runnables import RunnableConfig

from agent import setup_runnable
from auth import setup_memory, restore_memory

# Store image paths for cultural and rules images
CULTURAL_IMAGE_PATH = "bano_cultural.jpeg"  # Image 1: Children playing Bano
RULES_IMAGE_PATH = "bano_rules.jpeg"  # Image 2: Illustrated Bano rules
OPENER_IMAGE_PATH = "opener.jpg"  # Opener image

# Quiz questions database
QUIZ_QUESTIONS = [
    {
        "category": "rules",
        "question": "What is typically used as game pieces in Bano?",
        "options": ["Dice", "Marbles or bottle caps", "Playing cards", "Sticks"],
        "correct": 1
    },
    {
        "category": "history",
        "question": "In which country is Bano especially popular?",
        "options": ["Nigeria", "South Africa", "Kenya", "Egypt"],
        "correct": 2
    },
    {
        "category": "rules",
        "question": "What shape is typically drawn on the ground for Bano?",
        "options": ["Square", "Triangle", "Circle", "Line"],
        "correct": 2
    },
    {
        "category": "strategy",
        "question": "Which of these is NOT a common strategy in Bano?",
        "options": ["Blocking opponent's moves", "Making alliances with other players", "Aiming for central positions",
                    "Using multiple circles at once"],
        "correct": 3
    },
    {
        "category": "history",
        "question": "What traditional materials were historically used to mark Bano playing fields?",
        "options": ["Paint", "Chalk or charcoal", "Colored stones", "Wood markers"],
        "correct": 1
    },
    {
        "category": "culture",
        "question": "When is Bano traditionally played in many African communities?",
        "options": ["Only during formal competitions", "During religious ceremonies",
                    "In leisure time after daily tasks", "Only during harvest season"],
        "correct": 2
    },
    {
        "category": "regional",
        "question": "How might Bano gameplay differ between regions?",
        "options": ["Number of players allowed", "Size of the playing area", "Rules for capturing pieces",
                    "All of the above"],
        "correct": 3
    },
    {
        "category": "rules",
        "question": "What happens when a player loses all their pieces in a traditional Bano game?",
        "options": ["They immediately lose the game", "They can buy back pieces", "They wait until the next round",
                    "They become the judge"],
        "correct": 0
    },
    {
        "category": "culture",
        "question": "What social value is often taught through Bano?",
        "options": ["Individual competition", "Community cooperation", "Resource management", "All of the above"],
        "correct": 3
    }
]


def get_topic_description(topic):
    """Get a friendly description of the topic for the quiz introduction and appropriate image"""
    topic_lower = topic.lower()

    # Default is no image
    image_path = None

    if "play" in topic_lower or "rules" in topic_lower or "how to" in topic_lower:
        description = "Bano gameplay and rules"
        image_path = RULES_IMAGE_PATH
    elif "history" in topic_lower or "origin" in topic_lower:
        description = "the history of Bano"
    elif "region" in topic_lower or "country" in topic_lower or "where" in topic_lower:
        description = "where Bano is played"
        image_path = CULTURAL_IMAGE_PATH
    elif "story" in topic_lower or "memory" in topic_lower or "experience" in topic_lower:
        description = "Bano stories and experiences"
        image_path = CULTURAL_IMAGE_PATH
    elif "strategy" in topic_lower or "technique" in topic_lower or "winning" in topic_lower:
        description = "Bano strategies and techniques"
        image_path = RULES_IMAGE_PATH
    elif "culture" in topic_lower or "tradition" in topic_lower:
        description = "the cultural significance of Bano"
        image_path = CULTURAL_IMAGE_PATH
    else:
        description = "Bano"

    return description, image_path


async def select_relevant_quiz_questions(topic, count=3):
    """Select quiz questions relevant to the topic of conversation"""
    # Map topic keywords to categories
    keyword_to_category = {
        "play": "rules", "rules": "rules", "how to": "rules", "strategy": "strategy",
        "history": "history", "origin": "history", "culture": "culture",
        "region": "regional", "country": "regional", "where": "regional", "location": "regional",
        "kenya": "regional", "tanzania": "regional", "africa": "regional",
        "story": "culture", "memory": "culture", "experience": "culture"
    }

    # Determine categories based on keywords in topic
    categories = set()
    topic_lower = topic.lower()
    for keyword, category in keyword_to_category.items():
        if keyword in topic_lower:
            categories.add(category)

    # If no specific categories matched, use all categories
    if not categories:
        categories = {"rules", "history", "culture", "regional", "strategy"}

    # Filter questions by selected categories
    relevant_questions = [q for q in QUIZ_QUESTIONS if q["category"] in categories]

    # If no relevant questions, fall back to all questions
    if not relevant_questions:
        relevant_questions = QUIZ_QUESTIONS

    # Select the requested number of questions (random or ordered)
    import random
    selected = random.sample(relevant_questions, min(count, len(relevant_questions)))

    return selected


@cl.on_chat_start
async def on_chat_start():
    # First message - greeting and introduction
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    intro_text = (
        f"{greeting}! 👋🏽\n\n"
        "I'm *Simba*, your Bano buddy. I'm here to help you explore the exciting world of Bano! 🟢🎯\n"
        "Before we get started, may I know your name?"
    )

    # Send introduction
    await cl.Message(content=intro_text).send()

    # Create image objects and store them in user session
    # This ensures they're properly initialized when we need them
    try:
        opener_image = cl.Image(path=OPENER_IMAGE_PATH, name="opener", display="inline")
        cultural_image = cl.Image(path=CULTURAL_IMAGE_PATH, name="bano_cultural", display="inline")
        rules_image = cl.Image(path=RULES_IMAGE_PATH, name="bano_rules", display="inline")

        # Store images in user session
        cl.user_session.set("opener_image", opener_image)
        cl.user_session.set("cultural_image", cultural_image)
        cl.user_session.set("rules_image", rules_image)
    except Exception as e:
        # Handle image loading errors gracefully
        print(f"Error loading images: {e}")
        await cl.Message(content="Note: Some images might not display correctly.").send()

    # Set flag in user session to indicate we're waiting for the name
    cl.user_session.set("waiting_for_name", True)

    # Setup memory and runnable
    setup_memory()
    setup_runnable()


@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    restore_memory(thread)
    setup_runnable()


async def send_quiz_question(question_data):
    """Send a single quiz question with option buttons"""
    # Get current question number
    current_question = cl.user_session.get("current_quiz_question", 0)

    # Create option buttons
    actions = [
        cl.Action(
            name="quiz_answer",
            payload={"question": question_data["question"],
                     "selected_index": i,
                     "correct_index": question_data["correct"]},
            label=option
        ) for i, option in enumerate(question_data["options"])
    ]

    # Send the question with question number
    await cl.Message(
        content=f"🎮 **Question {current_question + 1}/3** 🎮\n\n{question_data['question']}",
        actions=actions
    ).send()


async def send_suggestions_after_quiz(topic):
    """Send follow-up suggestions after the quiz is complete"""
    # Determine appropriate follow-up questions based on the conversation context
    if "play" in topic or "rules" in topic or "how to" in topic:
        follow_ups = [
            {"question": "What are some winning strategies for Bano?", "label": "Winning strategies?"},
            {"question": "Are there different variations of Bano?", "label": "Game variations"},
            {"question": "What equipment do I need to play Bano?", "label": "Equipment needed"}
        ]
        # Suggest a new topic - history
        new_topic = {"question": "What's the history behind the game of Bano?", "label": "Explore Bano's history"}
    elif "history" in topic or "origin" in topic:
        follow_ups = [
            {"question": "What cultural significance does Bano have?", "label": "Cultural significance"},
            {"question": "Are there similar games in other cultures?", "label": "Similar games"},
            {"question": "How has Bano evolved over time?", "label": "Evolution of Bano"}
        ]
        # Suggest a new topic - regional variations
        new_topic = {"question": "Where is Bano mostly played, and what are the regional differences?",
                     "label": "Explore regional variations"}
    elif "region" in topic or "country" in topic or "where" in topic or "location" in topic:
        follow_ups = [
            {"question": "How is Bano played specifically in Kenya?", "label": "Kenyan style"},
            {"question": "How does Bano differ in Tanzania?", "label": "Tanzanian variations"},
            {"question": "Has Bano spread beyond East Africa?", "label": "Global reach"}
        ]
        # Suggest a new topic - stories
        new_topic = {"question": "Do you know any stories or memories people have about playing Bano?",
                     "label": "Discover Bano stories"}
    elif "story" in topic or "memory" in topic or "experience" in topic:
        follow_ups = [
            {"question": "Are there any famous Bano players?", "label": "Famous players"},
            {"question": "Are there Bano tournaments or competitions?", "label": "Tournaments"},
            {"question": "Can you share a story about a memorable Bano game?", "label": "Memorable games"}
        ]
        # Suggest a new topic - gameplay
        new_topic = {"question": "Can you explain how to play Bano, step by step?", "label": "Learn gameplay basics"}
    else:
        # Default follow-ups for general questions
        follow_ups = [
            {"question": "Can you explain the basic rules of Bano?", "label": "Basic rules"},
            {"question": "Why is Bano so popular in East Africa?", "label": "Popularity reasons"},
            {"question": "How can I learn to play Bano well?", "label": "Learning tips"}
        ]
        # Default new topic suggestion
        new_topic = {"question": "What's the history behind the game of Bano?", "label": "Explore Bano's history"}

    # Create action buttons for related follow-ups
    actions = [
        cl.Action(
            name="dynamic_suggestion",
            payload={"question": item["question"]},
            label=item["label"]
        )
        for item in follow_ups
    ]

    # Add the new topic suggestion with a special styling or indicator
    new_topic_action = cl.Action(
        name="new_topic_suggestion",
        payload={"question": new_topic["question"]},
        label="🔄 " + new_topic["label"] + " 🔄"  # Adding special emoji indicators
    )

    # Send follow-up suggestions with the new topic option
    suggestion_msg = cl.Message(content="Would you like to learn more about:", actions=actions)
    await suggestion_msg.send()

    # Send new topic suggestion as a separate message
    new_topic_msg = cl.Message(content="Or explore a new topic:", actions=[new_topic_action])
    await new_topic_msg.send()


@cl.on_message
async def on_message(message: cl.Message):
    # Check if we're waiting for the user's name
    waiting_for_name = cl.user_session.get("waiting_for_name", False)

    if waiting_for_name:
        # Store the user's name
        user_name = message.content
        cl.user_session.set("user_name", user_name)
        cl.user_session.set("waiting_for_name", False)

        # Get the opener image from user session
        opener_image = cl.user_session.get("opener_image")

        # Welcome message with image and personalized greeting
        welcome_text = (
            f"Nice to meet you, {user_name}! Welcome to the world of *Bano*! 🟢🎯\n\n"
            "Ready to dive into some nostalgic fun?\n"
            "You can ask me anything, or pick one of these to get started!👇"
        )

        # Send with image if available
        if opener_image:
            # FIXED: Include elements when creating the message, not when sending
            await cl.Message(content=welcome_text, elements=[opener_image]).send()
        else:
            await cl.Message(content=welcome_text).send()

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

        # Send message with actions
        suggestion_msg = cl.Message(content="Here are some ideas you can click on:", actions=actions)
        await suggestion_msg.send()

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

        # Send the response without images first
        await res.send()

        # Check if we should show an image based on the topic
        topic = message.content.lower()
        description, image_path = get_topic_description(topic)

        # Get appropriate image from user session based on topic
        topic_image = None
        if image_path == CULTURAL_IMAGE_PATH:
            topic_image = cl.user_session.get("cultural_image")
        elif image_path == RULES_IMAGE_PATH:
            topic_image = cl.user_session.get("rules_image")

        # If we have a relevant image, send it as a separate message
        if topic_image:
            # FIXED: Create the message with elements included
            image_message = cl.Message(
                content=f"Here's a visual to help you understand {description}:",
                elements=[topic_image]
            )
            await image_message.send()  # No elements parameter here

        # Update memory
        memory.chat_memory.add_user_message(message.content)
        memory.chat_memory.add_ai_message(res.content)

        # Generate follow-up suggestions based on the conversation context
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

        # Create action buttons
        actions = [
            cl.Action(
                name="dynamic_suggestion",
                payload={"question": item["question"]},
                label=item["label"]
            )
            for item in follow_ups
        ]

        # Add a quiz button
        actions.append(
            cl.Action(
                name="quiz_request",
                payload={"topic": topic},
                label="💡 Test your knowledge!"
            )
        )

        # Send follow-up suggestions as a separate message - ensure it has actions
        suggestion_msg = cl.Message(content="Would you like to know more about:", actions=actions)
        await suggestion_msg.send()


# Quiz functionality with image support
@cl.action_callback("quiz_request")
async def on_quiz_request(action):
    """Handle request for a quiz question"""
    topic = action.payload.get("topic", "")

    # Store the topic for later use
    cl.user_session.set("quiz_topic", topic)

    # Select 3 relevant quiz questions
    questions = await select_relevant_quiz_questions(topic, count=3)
    if questions:
        # Store the quiz questions and initialize quiz state
        cl.user_session.set("quiz_questions", questions)
        cl.user_session.set("current_quiz_question", 0)
        cl.user_session.set("quiz_score", 0)

        # Determine if an image is appropriate for this quiz topic
        description, image_path = get_topic_description(topic)

        # Get appropriate image from user session based on topic
        topic_image = None
        if image_path == CULTURAL_IMAGE_PATH:
            topic_image = cl.user_session.get("cultural_image")
        elif image_path == RULES_IMAGE_PATH:
            topic_image = cl.user_session.get("rules_image")

        # Start the quiz with the first question
        # FIXED: Create message with elements included if image is available
        if topic_image:
            quiz_intro = cl.Message(
                content=f"🎮 **Let's test your Bano knowledge with 3 questions about {description}!** 🎮",
                elements=[topic_image]
            )
        else:
            quiz_intro = cl.Message(
                content=f"🎮 **Let's test your Bano knowledge with 3 questions about {description}!** 🎮"
            )

        await quiz_intro.send()
        await send_quiz_question(questions[0])
    else:
        await cl.Message(content="Sorry, I don't have any quiz questions prepared for this topic yet.").send()


@cl.action_callback("quiz_answer")
async def on_quiz_answer(action):
    """Handle quiz answer selection"""
    question = action.payload.get("question", "")
    selected_index = action.payload.get("selected_index", -1)
    correct_index = action.payload.get("correct_index", -1)
    topic = cl.user_session.get("quiz_topic", "")

    # Retrieve quiz state
    quiz_questions = cl.user_session.get("quiz_questions", [])
    current_question_index = cl.user_session.get("current_quiz_question", 0)
    quiz_score = cl.user_session.get("quiz_score", 0)

    # Check if answer is correct
    is_correct = selected_index == correct_index

    # Update score if correct
    if is_correct:
        quiz_score += 1
        cl.user_session.set("quiz_score", quiz_score)
        await cl.Message(content=f"✅ Correct! Great job! 🎉").send()
    else:
        # Get correct option text
        correct_option = QUIZ_QUESTIONS[0]["options"][correct_index]  # Fallback
        for q in QUIZ_QUESTIONS:
            if q["question"] == question:
                correct_option = q["options"][correct_index]
                break

        await cl.Message(content=f"❌ Not quite! The correct answer is: **{correct_option}**").send()

    # Move to next question or finish quiz
    current_question_index += 1
    cl.user_session.set("current_quiz_question", current_question_index)

    # Check if we have more questions
    if current_question_index < len(quiz_questions) and current_question_index < 3:
        # Send next question
        await send_quiz_question(quiz_questions[current_question_index])
    else:
        # Quiz complete - show final score
        await cl.Message(
            content=f"🏆 **Quiz Complete!** 🏆\n\nYour score: **{quiz_score}/{min(len(quiz_questions), 3)}**\n\nWell done! Keep learning about Bano! 🎮").send()

        # After quiz is complete, show relevant follow-up suggestions again
        await send_suggestions_after_quiz(topic)


# New topic suggestion callback
@cl.action_callback("new_topic_suggestion")
async def on_new_topic_suggestion(action):
    """Handle clicks on new topic suggestions"""
    question = action.payload.get("question", "")
    if question:
        await on_message(cl.Message(content=question))


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