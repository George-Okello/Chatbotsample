from datetime import datetime
import json

import chainlit as cl
from langchain_core.runnables import RunnableConfig

from agent import setup_runnable, assess_user_knowledge, get_cultural_context
from agent import LEARNING_LEVELS, CULTURAL_CONTEXTS, ACTIVITY_COMPONENTS
from agent import adapt_content_to_level, identify_proximal_development_needs
from auth import setup_memory, restore_memory

# Store image paths for all images
CULTURAL_IMAGE_PATH = "bano_cultural.jpeg"  # Image 1: Children playing Bano
RULES_IMAGE_PATH = "bano_rules.jpeg"  # Image 2: Illustrated Bano rules
HISTORY_IMAGE_PATH = "bano_history.jpeg"  # Image 3: Historical context of Bano
OPENER_IMAGE_PATH = "opener.jpg"  # Opener image

# Quiz questions database - Enhanced with CHAT framework components
QUIZ_QUESTIONS = [
    {
        "category": "rules",
        "question": "What is typically used as game pieces in Bano?",
        "options": ["Dice", "Marbles or bottle caps", "Playing cards", "Sticks"],
        "correct": 1,
        "level": "novice",
        "activity_component": "tools"
    },
    {
        "category": "history",
        "question": "In which country is Bano especially popular?",
        "options": ["Nigeria", "South Africa", "Kenya", "Egypt"],
        "correct": 2,
        "level": "novice",
        "activity_component": "community"
    },
    {
        "category": "rules",
        "question": "What shape is typically drawn on the ground for Bano?",
        "options": ["Square", "Triangle", "Circle", "Line"],
        "correct": 2,
        "level": "novice",
        "activity_component": "tools"
    },
    {
        "category": "strategy",
        "question": "Which of these is NOT a common strategy in Bano?",
        "options": ["Blocking opponent's moves", "Making alliances with other players", "Aiming for central positions",
                    "Using multiple circles at once"],
        "correct": 3,
        "level": "intermediate",
        "activity_component": "rules"
    },
    {
        "category": "history",
        "question": "What traditional materials were historically used to mark Bano playing fields?",
        "options": ["Paint", "Chalk or charcoal", "Colored stones", "Wood markers"],
        "correct": 1,
        "level": "beginner",
        "activity_component": "tools"
    },
    {
        "category": "culture",
        "question": "When is Bano traditionally played in many African communities?",
        "options": ["Only during formal competitions", "During religious ceremonies",
                    "In leisure time after daily tasks", "Only during harvest season"],
        "correct": 2,
        "level": "beginner",
        "activity_component": "community"
    }
]

# CHAT Framework: Reflection questions to encourage higher-order thinking
REFLECTION_QUESTIONS = {
    "novice": [
        "How does Bano compare to games you've played before?",
        "What was your favorite part about learning Bano?",
        "How would you explain Bano to a friend?",
    ],
    "beginner": [
        "How might playing Bano help children develop skills?",
        "What similarities do you see between Bano and other cultural games?",
        "How do you think the environment affects how Bano is played?",
    ],
    "intermediate": [
        "How does Bano reflect the values of the communities that play it?",
        "In what ways might modern technology change how Bano is played or taught?",
        "How does Bano connect generations within a community?",
    ],
    "advanced": [
        "How has Bano evolved as a cultural activity system over time?",
        "What contradictions exist between traditional Bano play and modern adaptations?",
        "How could Bano be used as an educational tool beyond game strategies?",
    ]
}


def get_topic_description(topic):
    """Get a friendly description of the topic and appropriate image"""
    topic_lower = topic.lower()

    # Default is no image
    image_path = None

    if "play" in topic_lower or "rules" in topic_lower or "how to" in topic_lower:
        description = "Bano gameplay and rules"
        image_path = RULES_IMAGE_PATH
    elif "history" in topic_lower or "origin" in topic_lower or "past" in topic_lower or "ancient" in topic_lower:
        description = "the history of Bano"
        image_path = HISTORY_IMAGE_PATH
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


async def select_relevant_quiz_questions(topic, count=3, user_level="novice"):
    """Select quiz questions relevant to the topic of conversation and user level"""
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
    category_questions = [q for q in QUIZ_QUESTIONS if q.get("category", "") in categories]

    # If no relevant questions by category, fall back to all questions
    if not category_questions:
        category_questions = QUIZ_QUESTIONS

    # Get user's level
    user_level_index = list(LEARNING_LEVELS.keys()).index(user_level)

    # Filter by user level or below (avoid questions too advanced)
    level_index_max = min(user_level_index + 1, len(LEARNING_LEVELS) - 1)  # Allow one level higher for challenge
    available_levels = list(LEARNING_LEVELS.keys())[:level_index_max + 1]

    # Filter questions by appropriate level
    level_questions = [q for q in category_questions if q.get("level", "novice") in available_levels]

    # If no questions at appropriate level, fall back to category questions
    if not level_questions:
        level_questions = category_questions

    # Select the requested number of questions (random or ordered)
    import random
    selected = random.sample(level_questions, min(count, len(level_questions)))

    return selected


async def send_quiz_question(question_data):
    """Send a single quiz question with option buttons"""
    # Get current question number
    current_question = cl.user_session.get("current_quiz_question", 0)

    # CHAT Framework: Identify which activity component this question relates to
    activity_component = question_data.get("activity_component", "rules")
    component_description = ""

    if activity_component == "tools":
        component_description = "(This question relates to the tools used in Bano)"
    elif activity_component == "rules":
        component_description = "(This question relates to the rules that structure Bano gameplay)"
    elif activity_component == "community":
        component_description = "(This question relates to the community context of Bano)"
    elif activity_component == "division_of_labor":
        component_description = "(This question relates to roles within the Bano activity system)"
    elif activity_component == "object":
        component_description = "(This question relates to the goals and outcomes of Bano)"

    # Create option buttons
    actions = [
        cl.Action(
            name="quiz_answer",
            payload={"question": question_data["question"],
                     "selected_index": i,
                     "correct_index": question_data["correct"],
                     "activity_component": activity_component},
            label=option
        ) for i, option in enumerate(question_data["options"])
    ]

    # Send the question with question number and activity component context
    await cl.Message(
        content=f"🎮 **Question {current_question + 1}/3** 🎮\n\n{question_data['question']}\n\n{component_description}",
        actions=actions
    ).send()


async def send_reflection_question(topic):
    """Send a reflection question based on the user's current level"""
    # Get user profile
    user_profile = cl.user_session.get("user_profile", {"learning_level": "novice"})
    user_level = user_profile["learning_level"]

    # Get appropriate reflection questions for this level
    level_questions = REFLECTION_QUESTIONS.get(user_level, REFLECTION_QUESTIONS["novice"])

    # Select a question
    import random
    reflection_question = random.choice(level_questions)

    # Send as a message with a textbox for response
    await cl.Message(
        content=f"🤔 **Reflection Question** 🤔\n\n{reflection_question}\n\n(Type your thoughts below)",
    ).send()

    # Track that we're waiting for reflection
    cl.user_session.set("waiting_for_reflection", True)
    cl.user_session.set("current_reflection_question", reflection_question)


async def send_follow_up_suggestions(topic):
    """Send follow-up suggestions based on the topic using CHAT framework"""
    # Get user profile
    user_profile = cl.user_session.get("user_profile", {"learning_level": "novice"})
    user_level = user_profile["learning_level"]

    # CHAT Framework: Integration of activity system components
    # For each topic, consider different aspects of the activity system

    if "play" in topic or "rules" in topic or "how to" in topic:
        # TOOLS and RULES focus
        follow_ups = [
            {"question": "What are some winning strategies for Bano?",
             "label": "Winning strategies",
             "activity_component": "rules"},
            {"question": "Are there different variations of Bano?",
             "label": "Game variations",
             "activity_component": "rules"},
            {"question": "What materials are traditionally used as game pieces in Bano?",
             "label": "Traditional materials",
             "activity_component": "tools"}
        ]
    elif "history" in topic or "origin" in topic or "past" in topic:
        # HISTORICAL DEVELOPMENT focus
        follow_ups = [
            {"question": "What cultural significance does Bano have in different communities?",
             "label": "Cultural significance",
             "activity_component": "community"},
            {"question": "How has Bano evolved from earlier traditional games?",
             "label": "Historical evolution",
             "activity_component": "historical_development"},
            {"question": "What similar games exist across different cultures?",
             "label": "Cultural similarities",
             "activity_component": "historical_development"}
        ]
    elif "region" in topic or "country" in topic or "where" in topic:
        # COMMUNITY focus
        follow_ups = [
            {"question": "How is Bano integrated into daily life in Kenya?",
             "label": "Kenyan cultural context",
             "activity_component": "community"},
            {"question": "How do the rules of Bano vary across different regions?",
             "label": "Regional rule variations",
             "activity_component": "rules"},
            {"question": "How has globalization affected the spread of Bano?",
             "label": "Global influences",
             "activity_component": "community"}
        ]
    elif "story" in topic or "memory" in topic or "experience" in topic:
        # SUBJECTS and COMMUNITY focus
        follow_ups = [
            {"question": "How do Bano stories get passed down between generations?",
             "label": "Intergenerational learning",
             "activity_component": "division_of_labor"},
            {"question": "Are there any famous Bano players or tournaments?",
             "label": "Notable players",
             "activity_component": "subject"},
            {"question": "How does Bano connect people within communities?",
             "label": "Community bonds",
             "activity_component": "community"}
        ]
    else:
        # Default: Balance across activity system
        follow_ups = [
            {"question": "Can you explain the basic rules of Bano?",
             "label": "Basic rules",
             "activity_component": "rules"},
            {"question": "What materials do you need to play Bano?",
             "label": "Game materials",
             "activity_component": "tools"},
            {"question": "How do communities gather for Bano games?",
             "label": "Social context",
             "activity_component": "community"}
        ]

    # Create action buttons with activity system component indicators
    actions = [
        cl.Action(
            name="dynamic_suggestion",
            payload={"question": item["question"],
                     "activity_component": item["activity_component"]},
            label=item["label"]
        )
        for item in follow_ups
    ]

    # Add a quiz button with adaptive difficulty based on user level
    actions.append(
        cl.Action(
            name="quiz_request",
            payload={"topic": topic, "level": user_profile["learning_level"]},
            label="💡 Test your Bano knowledge!"
        )
    )

    # Send follow-up suggestions as a separate message
    suggestion_msg = cl.Message(content="Would you like to know more about:", actions=actions)
    await suggestion_msg.send()


@cl.on_chat_start
async def on_chat_start():
    # Initialize user profile with CHAT framework components
    user_profile = {
        "learning_level": "novice",  # Start everyone at novice level
        "cultural_context": "east_african",  # Default context
        "activity_focus": "rules",  # Initial focus on rules
        "quiz_history": [],
        "concepts_explored": [],
        "reflection_responses": []
    }

    # Store user profile in session
    cl.user_session.set("user_profile", user_profile)

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
    try:
        opener_image = cl.Image(path=OPENER_IMAGE_PATH, name="opener", display="inline")
        cultural_image = cl.Image(path=CULTURAL_IMAGE_PATH, name="bano_cultural", display="inline")
        rules_image = cl.Image(path=RULES_IMAGE_PATH, name="bano_rules", display="inline")
        history_image = cl.Image(path=HISTORY_IMAGE_PATH, name="bano_history", display="inline")

        # Store images in user session
        cl.user_session.set("opener_image", opener_image)
        cl.user_session.set("cultural_image", cultural_image)
        cl.user_session.set("rules_image", rules_image)
        cl.user_session.set("history_image", history_image)
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

    # Restore user profile or create a new one if needed
    if not cl.user_session.get("user_profile"):
        user_profile = {
            "learning_level": "novice",
            "cultural_context": "east_african",
            "activity_focus": "rules",
            "quiz_history": [],
            "concepts_explored": [],
            "reflection_responses": []
        }
        cl.user_session.set("user_profile", user_profile)


@cl.on_message
async def on_message(message: cl.Message):
    # Check if we're waiting for the user's name
    waiting_for_name = cl.user_session.get("waiting_for_name", False)
    waiting_for_reflection = cl.user_session.get("waiting_for_reflection", False)

    if waiting_for_name:
        # Store the user's name
        user_name = message.content.strip()
        cl.user_session.set("user_name", user_name)
        cl.user_session.set("waiting_for_name", False)

        # Get the opener image from user session
        opener_image = cl.user_session.get("opener_image")

        # Welcome message with personalized greeting
        welcome_text = (
            f"Nice to meet you, {user_name}! Welcome to the world of *Bano*! 🟢🎯\n\n"
            "Ready to dive into some nostalgic fun?\n"
            "You can ask me anything, or pick one of these to get started!👇"
        )

        # Send welcome message with image if available
        if opener_image:
            welcome_msg = cl.Message(content=welcome_text, elements=[opener_image])
        else:
            welcome_msg = cl.Message(content=welcome_text)

        await welcome_msg.send()

        # CHAT Framework: Initial suggested questions cover different aspects of the activity system
        actions = [
            cl.Action(
                name="dynamic_suggestion",
                payload={"question": "Can you explain how to play Bano, step by step?",
                         "activity_component": "rules"},
                label="📏 How is Bano played?"
            ),
            cl.Action(
                name="dynamic_suggestion",
                payload={"question": "What materials are traditionally used to play Bano?",
                         "activity_component": "tools"},
                label="🧰 What materials are used?"
            ),
            cl.Action(
                name="dynamic_suggestion",
                payload={"question": "How does Bano bring communities together?",
                         "activity_component": "community"},
                label="👥 Social aspects of Bano"
            ),
            cl.Action(
                name="dynamic_suggestion",
                payload={"question": "How has Bano evolved throughout history?",
                         "activity_component": "historical_development"},
                label="📜 Historical development"
            ),
            cl.Action(
                name="dynamic_suggestion",
                payload={"question": "What skills does playing Bano help develop?",
                         "activity_component": "object"},
                label="🎯 Skills and outcomes"
            )
        ]

        # Send message with actions
        suggestion_msg = cl.Message(content="Here are some aspects of Bano you can explore:", actions=actions)
        await suggestion_msg.send()

    elif waiting_for_reflection:
        # Store user's reflection response
        reflection_question = cl.user_session.get("current_reflection_question", "")
        user_profile = cl.user_session.get("user_profile", {})

        # Add reflection response to user profile
        if "reflection_responses" not in user_profile:
            user_profile["reflection_responses"] = []

        user_profile["reflection_responses"].append({
            "question": reflection_question,
            "response": message.content,
            "timestamp": str(datetime.now())
        })

        # Update user profile
        cl.user_session.set("user_profile", user_profile)
        cl.user_session.set("waiting_for_reflection", False)

        # CHAT Framework: Acknowledge reflection and provide feedback
        await cl.Message(
            content="Thank you for sharing your reflection! 🌟\n\nThinking about Bano in this way helps deepen understanding of both the game and its cultural significance. Let's continue exploring!"
        ).send()

        # Redirect to regular conversation flow
        await on_message(cl.Message(content="Let's continue our Bano discussion"))

    else:
        # Normal message handling
        memory = cl.user_session.get("memory")
        runnable = cl.user_session.get("runnable")
        user_name = cl.user_session.get("user_name", "there")  # Default fallback

        # CHAT Framework: Update user profile based on interaction
        # Get current user profile
        user_profile = cl.user_session.get("user_profile", {
            "learning_level": "novice",
            "cultural_context": "east_african",
            "activity_focus": "rules",
            "quiz_history": [],
            "concepts_explored": [],
            "reflection_responses": []
        })

        # Update learning level based on conversation
        if memory and hasattr(memory, 'chat_memory'):
            conversation_history = memory.chat_memory.messages
            user_profile["learning_level"] = assess_user_knowledge(conversation_history, message.content)
            user_profile["cultural_context"] = get_cultural_context(conversation_history)

        # Store updated profile
        cl.user_session.set("user_profile", user_profile)

        # Update context with user profile information and name
        context = {
            "question": message.content,
            "user_name": user_name,
            "user_level": user_profile["learning_level"],
            "cultural_context": user_profile["cultural_context"]
        }

        # Create a message for the response
        res = cl.Message(content="")

        # Stream the response
        async for chunk in runnable.astream(
                context,
                config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()])
        ):
            await res.stream_token(chunk)

        # Get the final content from the streamed response
        final_content = res.content

        # Apply the adaptation
        adapted_content = adapt_content_to_level(final_content, user_profile["learning_level"])

        # Instead of updating the existing message (which causes the error),
        # we'll send a new message with the adapted content
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
        elif image_path == HISTORY_IMAGE_PATH:
            topic_image = cl.user_session.get("history_image")

        # If we have a relevant image, send it as a separate message
        if topic_image:
            image_message = cl.Message(
                content=f"Here's a visual to help you understand {description}:",
                elements=[topic_image]
            )
            await image_message.send()

        # Update memory
        memory.chat_memory.add_user_message(message.content)
        memory.chat_memory.add_ai_message(adapted_content)

        # Track explored concepts in user profile
        topic_lower = topic.lower()
        if "rules" in topic_lower or "how to" in topic_lower or "play" in topic_lower:
            user_profile["activity_focus"] = "rules"
            if "concepts_explored" not in user_profile:
                user_profile["concepts_explored"] = []
            if "rules" not in user_profile["concepts_explored"]:
                user_profile["concepts_explored"].append("rules")

        # Update user profile
        cl.user_session.set("user_profile", user_profile)

        # Send follow-up suggestions
        await send_follow_up_suggestions(topic)


# Quiz functionality with CHAT framework integration
@cl.action_callback("quiz_request")
async def on_quiz_request(action):
    """Handle request for a quiz question with adaptive difficulty"""
    topic = action.payload.get("topic", "")
    requested_level = action.payload.get("level", "novice")

    # Store the topic for later use
    cl.user_session.set("quiz_topic", topic)

    # Get user profile
    user_profile = cl.user_session.get("user_profile", {"learning_level": "novice"})

    # Use requested level or fall back to user's current level
    quiz_level = requested_level if requested_level else user_profile["learning_level"]

    # Select 3 relevant quiz questions based on user's level
    questions = await select_relevant_quiz_questions(topic, count=3, user_level=quiz_level)
    if questions:
        # Store the quiz questions and initialize quiz state
        cl.user_session.set("quiz_questions", questions)
        cl.user_session.set("current_quiz_question", 0)
        cl.user_session.set("quiz_score", 0)
        cl.user_session.set("quiz_total", len(questions))

        # Determine if an image is appropriate for this quiz topic
        description, image_path = get_topic_description(topic)

        # Get appropriate image from user session based on topic
        topic_image = None
        if image_path == CULTURAL_IMAGE_PATH:
            topic_image = cl.user_session.get("cultural_image")
        elif image_path == RULES_IMAGE_PATH:
            topic_image = cl.user_session.get("rules_image")
        elif image_path == HISTORY_IMAGE_PATH:
            topic_image = cl.user_session.get("history_image")

        # CHAT Framework: Introduce quiz with appropriate scaffolding based on level
        level_text = ""
        if quiz_level == "novice":
            level_text = "These questions will help you start understanding the basics of Bano."
        elif quiz_level == "beginner":
            level_text = "These questions will help reinforce your understanding of Bano fundamentals."
        elif quiz_level == "intermediate":
            level_text = "These questions will challenge your growing knowledge of Bano's complexity."
        elif quiz_level == "advanced":
            level_text = "These questions will test your expert knowledge of Bano's nuances."

        # Start the quiz with the first question
        if topic_image:
            quiz_intro = cl.Message(
                content=f"🎮 **Let's test your Bano knowledge with 3 questions about {description}!** 🎮\n\n{level_text}",
                elements=[topic_image]
            )
        else:
            quiz_intro = cl.Message(
                content=f"🎮 **Let's test your Bano knowledge with 3 questions about {description}!** 🎮\n\n{level_text}"
            )

        await quiz_intro.send()
        await send_quiz_question(questions[0])
    else:
        await cl.Message(content="Sorry, I don't have any quiz questions prepared for this topic yet.").send()


@cl.action_callback("quiz_answer")
async def on_quiz_answer(action):
    """Handle quiz answer selection with CHAT framework feedback"""
    question = action.payload.get("question", "")
    selected_index = action.payload.get("selected_index", -1)
    correct_index = action.payload.get("correct_index", -1)
    activity_component = action.payload.get("activity_component", "rules")
    topic = cl.user_session.get("quiz_topic", "")

    # Retrieve quiz state
    quiz_questions = cl.user_session.get("quiz_questions", [])
    current_question_index = cl.user_session.get("current_quiz_question", 0)
    quiz_score = cl.user_session.get("quiz_score", 0)

    # Get user profile for adaptive feedback
    user_profile = cl.user_session.get("user_profile", {"learning_level": "novice"})
    user_level = user_profile["learning_level"]

    # Check if answer is correct
    is_correct = selected_index == correct_index

    # CHAT Framework: Track quiz history in user profile
    if "quiz_history" not in user_profile:
        user_profile["quiz_history"] = []

    user_profile["quiz_history"].append({
        "question": question,
        "selected_index": selected_index,
        "correct_index": correct_index,
        "is_correct": is_correct,
        "activity_component": activity_component,
        "timestamp": str(datetime.now())
    })

    # Update user profile
    cl.user_session.set("user_profile", user_profile)

    # Update score if correct
    if is_correct:
        quiz_score += 1
        cl.user_session.set("quiz_score", quiz_score)

        # Provide encouraging feedback
        await cl.Message(content=f"✅ Correct! Great job! 🎉").send()
    else:
        # Get correct option text
        correct_option = "Unknown"  # Default
        for q in quiz_questions:
            if q["question"] == question:
                correct_option = q["options"][correct_index]
                break

        # Provide constructive feedback
        await cl.Message(content=f"❌ Not quite! The correct answer is: **{correct_option}**").send()

    # Move to next question or finish quiz
    current_question_index += 1
    cl.user_session.set("current_quiz_question", current_question_index)

    # Check if we have more questions
    if current_question_index < len(quiz_questions) and current_question_index < 3:
        # Send next question
        await send_quiz_question(quiz_questions[current_question_index])
    else:
        # Quiz complete - show final score with adaptive feedback
        score_percentage = quiz_score / min(len(quiz_questions), 3) * 100

        # CHAT Framework: Provide adaptive summary based on score
        if score_percentage >= 80:
            feedback = "Excellent work! You're demonstrating a strong understanding of Bano!"
        elif score_percentage >= 50:
            feedback = "Good effort! You're building your Bano knowledge well."
        else:
            feedback = "Keep learning! Bano has many aspects to explore."

        # Send quiz completion message
        await cl.Message(
            content=f"🏆 **Quiz Complete!** 🏆\n\nYour score: **{quiz_score}/{min(len(quiz_questions), 3)}**\n\n{feedback}").send()

        # After quiz is complete, show relevant follow-up suggestions again
        await send_follow_up_suggestions(topic)

        # CHAT Framework: Add reflection question after quiz
        await send_reflection_question(topic)


@cl.action_callback("reflection_request")
async def on_reflection_request(action):
    """Handle request for reflection questions"""
    topic = action.payload.get("topic", "")

    # Send a reflection question
    await send_reflection_question(topic)


# Dynamic suggestion callback
@cl.action_callback("dynamic_suggestion")
async def on_dynamic_suggestion_action(action):
    """Handle clicks on dynamic suggestions with activity components"""
    question = action.payload.get("question", "")
    activity_component = action.payload.get("activity_component", "")

    if question:
        # Update user profile to note this activity component is being explored
        user_profile = cl.user_session.get("user_profile", {})
        user_profile["activity_focus"] = activity_component
        cl.user_session.set("user_profile", user_profile)

        # Process the message
        await on_message(cl.Message(content=question))