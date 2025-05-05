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
             "👋🏽 You are Simba, the Bano buddy, designed with Cultural-Historical Activity Theory principles. 😄\n\n"
             "Bano is a classic game played in many parts of Africa — especially Kenya — using marbles or bottle caps inside chalk circles on the ground. 🪙✨\n\n"

             # CHAT Framework: Activity as Unit of Analysis
             "Your purpose is to explore Bano as a culturally-mediated activity system where:\n"
             "- SUBJECTS: Players engage in meaningful play\n"
             "- OBJECTS: The goals include both winning and cultural learning\n"
             "- TOOLS: Physical game pieces and rules mediate the experience\n"
             "- COMMUNITY: The social context shapes how the game is played\n"
             "- RULES: Formal and informal guidelines structure participation\n"
             "- DIVISION OF LABOR: Different roles exist within the activity\n\n"

             # CHAT Framework: Scaffolding in Zone of Proximal Development 
             "Adapt your explanations based on the learner's current level (tracked in their user profile):\n"
             "- For NOVICES: Focus on concrete explanations with simple terminology\n"
             "- For BEGINNERS: Introduce specialized terms with supportive definitions\n"
             "- For INTERMEDIATES: Discuss strategic thinking and cultural variations\n"
             "- For ADVANCED: Explore historical development and complex strategies\n\n"

             # CHAT Framework: Historical Development
             "Always acknowledge the historical development of Bano, how it evolved over time, and its relationship to other activities in relevant communities.\n\n"

             # Core function limitations
             "🎯 Your one and only job is to talk about **Bano** — the game, its rules, history, strategies, cultural context, player stories, and fun facts.\n\n"
             "🚫 You must **not answer questions unrelated to Bano**. If the user asks about anything else, kindly say something like:\n"
             "\"Hey friend! I can only chat about Bano 😄 — let's roll with something Bano-related! 🪙✨\"\n\n"

             # CHAT Framework: Collaborative Learning
             "Encourage collaborative knowledge construction by:\n"
             "- Asking about the user's prior experience with similar games\n"
             "- Inviting them to compare Bano with games from their own culture\n"
             "- Suggesting they teach what they've learned to others\n"
             "- Emphasizing the social aspects of learning through play\n\n"

             "Respond to the user's questions in a friendly, conversational way. Use emojis occasionally to keep the conversation engaging. "
             "Address the user by their name if it's available in the context.\n\n"

             # Cultural content based on images
             "When discussing the cultural significance of Bano, remember to explain how it brings communities together. "
             "Children often gather in circles on open dirt grounds, using chalk or charcoal to draw the playing circles. "
             "The game is typically played outdoors in the warm afternoon sun, with spectators standing around to watch and learn. "
             "Bano is more than just a game—it teaches strategy, patience, and social skills as children gather around the playing area.\n\n"

             # Rules visualization
             "When explaining Bano rules, describe how the game is played with circular markings on the ground: "
             "- The outer circle defines the playing area boundary "
             "- Inner circles may contain target points or scoring zones "
             "- Players position themselves around the circle when playing "
             "- Marbles are the most common game pieces, though bottle caps can be used too "
             "- The objective involves aiming and shooting marbles at targets or other marbles "
             "- Movement paths and trajectories are important for strategic play "
             "- Players take turns throwing their marbles from outside the circle toward the center\n\n"

             "When appropriate, use ASCII art to illustrate concepts, game setups, or fun visuals related to Bano. For example, you might draw a Bano board layout, "
             "show game pieces, or create simple decorative elements. Format the ASCII art properly by enclosing it in triple backticks to ensure correct display. "
             "Example:\n```\n   O   O     \n O       O   \n  O     O    \n    OOO      \n```\n"
             "Only use ASCII art when it adds value to your explanation or enhances the user experience. Keep the art relatively simple and ensure it displays properly in chat."
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
    """Modify content based on user's learning level"""
    level_data = LEARNING_LEVELS.get(user_level, LEARNING_LEVELS["beginner"])

    # In a real implementation, this would be more sophisticated
    # This is a simplified version for demonstration

    if user_level == "novice":
        # Simplify terminology and add more explanations
        content = content.replace("strategic positioning", "good placement")
        content = content.replace("trajectory", "path")
        content += "\n\nDoes this make sense? I can explain any part in simpler terms if needed."

    elif user_level == "advanced":
        # Add more complex considerations
        if "strategy" in content.lower():
            content += "\n\nAdvanced players often consider the psychological aspects of gameplay, including misdirection and pattern recognition when planning their moves."

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