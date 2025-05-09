# Enhanced agent.py with Cultural-Historical Activity Theory (CHAT) Framework
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

# CHAT Framework: Define learning levels for scaffolding
LEARNING_LEVELS = {
    "novice": {
        "description": "New to Bano with no prior knowledge",
        "complexity": 1,
        "explanation_depth": "basic",
        "terminology": "simple",
        "cultural_context": "introductory"
    },
    "beginner": {
        "description": "Familiar with basic Bano concepts",
        "complexity": 2,
        "explanation_depth": "expanded",
        "terminology": "introducing specialized terms",
        "cultural_context": "more detailed"
    },
    "intermediate": {
        "description": "Understands rules and basic strategies",
        "complexity": 3,
        "explanation_depth": "detailed",
        "terminology": "using specialized terms",
        "cultural_context": "specific regional variations"
    },
    "advanced": {
        "description": "Experienced player seeking deeper insights",
        "complexity": 4,
        "explanation_depth": "comprehensive",
        "terminology": "technical",
        "cultural_context": "historical and sociological perspectives"
    }
}

# CHAT Framework: Define cultural contexts for mediation
CULTURAL_CONTEXTS = {
    "east_african": {
        "regions": ["Kenya", "Tanzania", "Uganda"],
        "terminology": {
            "game": "Bano",
            "marbles": "dende",
            "play area": "uwanja wa bano"
        },
        "cultural_significance": "Community building, intergenerational play",
        "historical_context": "Traditionally played after harvest season"
    },
    "west_african": {
        "regions": ["Nigeria", "Ghana"],
        "terminology": {
            "game": "Okwe",
            "marbles": "okuta",
            "play area": "papa okwe"
        },
        "cultural_significance": "Strategic thinking, patience development",
        "historical_context": "Often played by elders to teach youth"
    },
    "southern_african": {
        "regions": ["South Africa", "Zimbabwe", "Botswana"],
        "terminology": {
            "game": "Moraba-raba",
            "marbles": "diketo",
            "play area": "sehala sa papadi"
        },
        "cultural_significance": "Problem-solving, mathematical thinking",
        "historical_context": "Connected to cattle herding traditions"
    }
}

# CHAT Framework: Activity System Components
ACTIVITY_COMPONENTS = {
    "subject": ["individual player", "team", "community"],
    "object": ["winning the game", "learning strategies", "social connection", "preserving tradition"],
    "tools": ["marbles", "bottle caps", "chalk/charcoal", "ground markings", "game rules"],
    "community": ["family", "neighborhood", "school", "cultural group"],
    "rules": ["turn-taking", "scoring", "piece movement", "game setup"],
    "division_of_labor": ["player roles", "teacher-learner", "expert-novice", "referee"]
}


def setup_runnable() -> Runnable:
    memory = user_session.get("memory")  # type: ConversationBufferMemory
    model = ChatCohere(streaming=True)

    # Enhanced system prompt with CHAT framework integration
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "👋🏽 You are Simba, the Bano buddy - a friendly childhood game expert! 😄\n\n"
             "Remember, you're chatting with a friend about Bano, so keep it natural and conversational. "
             "Think of yourself as that cool friend who loves sharing fun memories about games!\n\n"

             # CONVERSATIONAL STYLE GUIDELINES
             "IMPORTANT CONVERSATIONAL PRINCIPLES:\n"
             "1. 💬 KEEP IT NATURAL - Aim for a friendly chat flow, keeping responses digestible\n"
             "2. 🤝 BE CONVERSATIONAL - Use everyday language, contractions, and a friendly tone\n"
             "3. ❓ ASK FOLLOW-UP QUESTIONS - Get the user talking and engaged\n"
             "4. 😊 USE EMOJIS NATURALLY - But don't overdo it (1-2 per response)\n"
             "5. 🎯 LISTEN AND RESPOND - Reply to what they're saying, not what you think they should know\n"
             "6. 🗣️ BE HUMAN-LIKE - Use expressions like \"you know,\" \"actually,\" \"by the way\"\n"
             "7. 🎨 DRAW EXPLANATIONS - Always create ASCII art when explaining rules or gameplay!\n\n"

             # RESPONSE LENGTH GUIDELINES
             "- For simple questions: Quick and direct (few sentences)\n"
             "- For explanations: Provide what's needed but keep it conversational\n"
             "- For complex topics: Break into chunks, use ASCII art, invite follow-ups\n"
             "- Always end with something to keep the conversation going\n"
             "- Trust your judgment - if they need more detail, give it!\n\n"

             # ASCII ART REQUIREMENT
             "🖍️ ASCII ART CREATION:\n"
             "- ALWAYS create ASCII art when explaining rules or gameplay\n"
             "- Generate unique diagrams based on what the user asks\n"
             "- Use it to illustrate your points visually\n"
             "- Make it simple but clear\n"
             "- Include labels and arrows when needed\n\n"

             # CHAT Framework: Activity as Unit of Analysis (simplified for conversation)
             "Your knowledge base covers Bano as:\n"
             "- A fun social game played across Africa\n"
             "- Using simple materials like marbles and chalk circles\n"
             "- Bringing communities together through play\n"
             "- Having different variations in different regions\n\n"

             # AVOID THESE CONVERSATION KILLERS
             "❌ DON'T INFO-DUMP - No walls of text\n"
             "❌ DON'T OVER-EXPLAIN - They'll ask if they want more\n"
             "❌ DON'T BE TOO FORMAL - You're not a textbook\n"
             "❌ DON'T LECTURE - Have a back-and-forth chat\n\n"

             # Core function
             "🎯 Your job is chatting about **Bano** - the game, stories, memories, and fun facts.\n\n"
             "🚫 For non-Bano topics, keep it light: \"Haha, let's stick to Bano! Got any favorite childhood games? 😄🪙\"\n\n"

             # CONVERSATION EXAMPLES
             "Good responses:\n"
             "- \"Oh, Bano! It's like marbles meets hopscotch. You draw circles and try to hit targets. Ever played anything similar?\"\n"
             "- \"Totally! Kids love it because it's simple but gets competitive quickly 😅\"\n"
             "- \"Exactly! In Kenya we call it Bano, but I think Tanzania has a similar version...\"\n\n"

             "REMEMBER: You're here to have fun conversations about Bano, not deliver lectures! 🎉"
             ),
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


# CHAT Framework: Helper functions for scaffolding user learning

def assess_user_knowledge(conversation_history, topic):
    """Analyze conversation to determine user's knowledge level for scaffolding"""
    # This would be more sophisticated in a real implementation
    # Currently simplified for demonstration

    if not conversation_history:
        return "novice"

    message_count = len(conversation_history)
    quiz_score = user_session.get("quiz_score", 0)
    quiz_total = user_session.get("quiz_total", 0)

    # Count domain-specific terminology used by user
    terminology_used = 0
    advanced_concepts = ["strategy", "tournament", "variation", "history", "cultural"]

    for msg in conversation_history:
        if hasattr(msg, "type") and msg.type == "human":
            content = msg.content.lower()
            terminology_used += sum(1 for term in advanced_concepts if term in content)

    # Simple heuristic to determine level
    if message_count < 3:
        return "novice"
    elif message_count < 6 or terminology_used < 2:
        return "beginner"
    elif message_count < 10 or (quiz_total > 0 and quiz_score / quiz_total < 0.7):
        return "intermediate"
    else:
        return "advanced"


def get_cultural_context(conversation_history):
    """Determine most relevant cultural context based on conversation"""
    # Default to East African (Kenyan) context
    default_context = "east_african"

    if not conversation_history:
        return default_context

    # Check for mentions of specific regions
    region_mentions = {
        "east_african": 0,
        "west_african": 0,
        "southern_african": 0
    }

    for msg in conversation_history:
        if hasattr(msg, "type") and msg.type == "human":
            content = msg.content.lower()

            # Count mentions of regions
            for context, data in CULTURAL_CONTEXTS.items():
                for region in data["regions"]:
                    if region.lower() in content:
                        region_mentions[context] += 1

    # Find most mentioned context
    most_mentioned = max(region_mentions.items(), key=lambda x: x[1])

    # If no specific mentions, use default
    if most_mentioned[1] == 0:
        return default_context

    return most_mentioned[0]


def adapt_content_to_level(content, user_level):
    """Modify content based on user's learning level - keeping it conversational"""
    level_data = LEARNING_LEVELS.get(user_level, LEARNING_LEVELS["beginner"])

    # Use level_data to determine how to adapt the content
    explanation_depth = level_data.get("explanation_depth", "basic")
    terminology = level_data.get("terminology", "simple")
    cultural_context = level_data.get("cultural_context", "introductory")

    # Adapt based on explanation depth
    if explanation_depth == "basic":
        # Keep it super simple
        content = content.replace("strategic positioning", "where you place your marble")
        content = content.replace("trajectory", "how it moves")
        content = content.replace("intricate", "detailed")

        # Only add clarification if response is getting complex
        if len(content.split()) > 30:
            content += " Make sense?"

    elif explanation_depth == "expanded":
        # Add a bit more detail but keep it friendly
        content = content.replace("strategic positioning", "where you place your marble (that's strategy!)")
        content = content.replace("trajectory", "path it takes")

    elif explanation_depth == "detailed":
        # Keep technical terms but add casual explanations
        if "strategy" in content.lower() and len(content.split()) < 40:
            content += " You probably know about reading the angles and stuff too."

    elif explanation_depth == "comprehensive":
        # Add depth but keep it conversational
        if "strategy" in content.lower() and len(content.split()) < 50:
            content += " You probably know about the mind games too, right?"

    # Adapt terminology based on level
    if terminology == "simple":
        # Replace complex terms with simple ones
        content = content.replace("traditional methodology", "old ways of playing")
        content = content.replace("cultural significance", "why it's important")
        content = content.replace("intergenerational", "between different ages")

    elif terminology == "introducing specialized terms":
        # Keep terms but add explanations
        specialized_terms = ["trajectory", "strategy", "cultural", "traditional"]
        for term in specialized_terms:
            if term in content.lower() and f"({term}" not in content.lower():
                content = content.replace(term, f"{term} (game term)")

    # Adapt cultural context if needed
    if cultural_context == "introductory":
        # Keep cultural references simple
        content = content.replace("East African tradition", "how they play in Kenya")
        content = content.replace("dialectical variations", "different ways to play")

    elif cultural_context == "specific regional variations":
        # Add regional details when appropriate
        if "regions" in content.lower() or "countries" in content.lower():
            content += " Different areas have their own special rules, you know."

    # Always trim if response is getting too long
    if len(content.split()) > 40:
        sentences = content.split('.')
        if len(sentences) > 2:
            content = '. '.join(sentences[:2]) + "."
            content += " Want to know more about any specific part?"

    return content


def identify_proximal_development_needs(conversation_history, user_level):
    """Identify what concepts the user is ready to learn next"""
    # ZPD concepts by level
    zpd_concepts = {
        "novice": ["basic rules", "turn taking", "simple scoring"],
        "beginner": ["basic strategy", "game variations", "cultural context"],
        "intermediate": ["advanced tactics", "regional differences", "historical context"],
        "advanced": ["psychological aspects", "teaching methods", "tournament play"]
    }

    # Get concepts for the next level
    current_level_index = list(LEARNING_LEVELS.keys()).index(user_level)
    if current_level_index < len(LEARNING_LEVELS) - 1:
        next_level = list(LEARNING_LEVELS.keys())[current_level_index + 1]
        target_concepts = zpd_concepts[next_level]
    else:
        # Already at highest level
        target_concepts = zpd_concepts["advanced"]

    # Filter for concepts not yet discussed
    discussed_concepts = []
    for msg in conversation_history:
        if hasattr(msg, "content"):
            content = msg.content.lower()
            discussed_concepts.extend([concept for concept in target_concepts
                                       if concept in content])

    # Return concepts in ZPD not yet discussed
    new_concepts = [concept for concept in target_concepts
                    if concept not in discussed_concepts]

    return new_concepts[:2]  # Return top 2 concepts