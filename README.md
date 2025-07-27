# Bano Game Chatbot - Technical Documentation

## Overview

The Bano Game Chatbot is an educational AI assistant built with **Chainlit** and **LangChain** that teaches users about Bano, a traditional African marble game. The chatbot implements the Cultural-Historical Activity Theory (CHAT) framework to provide adaptive, culturally-aware learning experiences.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technical Components](#technical-components)
- [API References](#api-references)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Features

### Core Functionality
- **Conversational AI**: Natural language interaction about Bano game rules, history, and culture
- **Adaptive Learning**: CHAT framework implementation with 4 learning levels (novice to advanced)
- **Cultural Context**: Multi-regional African cultural variations (East, West, Southern Africa)
- **Interactive Quizzes**: Dynamic quiz generation based on conversation topics
- **Visual Learning**: ASCII art generation for game rules and setup
- **Multimedia Support**: Images and videos for enhanced learning experience
- **Memory Management**: Conversation history persistence across sessions

### Educational Features
- **Scaffolded Learning**: Zone of Proximal Development (ZPD) based content adaptation
- **Reflection Questions**: Level-appropriate reflection prompts
- **Cultural Sensitivity**: Region-specific terminology and cultural context
- **Progress Tracking**: User learning analytics and quiz performance tracking

## Architecture

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chainlit UI   │────│  Main Handler   │────│  Agent Module   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Authentication  │    │ Memory Manager  │    │ CHAT Framework  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Media Assets  │    │ Quiz System     │    │ Search Tools    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack
- **Framework**: Chainlit 1.0+
- **LLM Integration**: LangChain + Cohere API
- **Search**: SerpAPI for real-time information
- **Memory**: ConversationBufferMemory
- **Authentication**: OAuth integration
- **Media**: Image/Video support for educational content

## Installation

### Prerequisites
- Python 3.8+
- pip package manager
- API keys for Cohere and SerpAPI

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd bano-chatbot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Required Packages**
   ```bash
   pip install chainlit langchain langchain-cohere langchain-community python-dotenv
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Keys
COHERE_API_KEY=your_cohere_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here

# Optional: Chainlit Configuration
CHAINLIT_AUTH_SECRET=your_auth_secret_here
```

### Media Assets Setup

Place the following media files in the project root directory:

```
project-root/
├── bano_cultural.jpeg    # Cultural context image
├── bano_rules.jpeg       # Game rules illustration
├── bano_history.jpeg     # Historical context image
├── opener.jpg           # Welcome screen image
└── gameplay.mp4         # Gameplay demonstration video
```

### API Keys Setup

1. **Cohere API Key**:
   - Visit [Cohere Dashboard](https://dashboard.cohere.ai/)
   - Create account and generate API key
   - Add to `.env` file

2. **SerpAPI Key**:
   - Visit [SerpAPI](https://serpapi.com/)
   - Create account and get API key
   - Add to `.env` file

## Usage

### Starting the Application

```bash
chainlit run main.py -w
```

The application will start on `http://localhost:8000`

### User Interaction Flow

1. **Welcome Phase**: User provides name and gets introduction
2. **Learning Phase**: Adaptive content delivery based on CHAT framework
3. **Assessment Phase**: Interactive quizzes and reflection questions
4. **Follow-up Phase**: Dynamic suggestions for continued learning

### Command Examples

```python
# Start a new chat session
chainlit run main.py

# Run with specific port
chainlit run main.py -p 8080

# Run in production mode
chainlit run main.py --host 0.0.0.0 --port 8000
```

## Project Structure

```
bano-chatbot/
├── main.py              # Main application entry point
├── agent.py             # Core agent logic with CHAT framework
├── auth.py              # Authentication and memory management
├── opener.py            # Initial setup and runnable configuration
├── .env                 # Environment variables (create this)
├── requirements.txt     # Python dependencies
├── README.md           # This documentation
├── media/              # Media assets directory
│   ├── bano_cultural.jpeg
│   ├── bano_rules.jpeg
│   ├── bano_history.jpeg
│   ├── opener.jpg
│   └── gameplay.mp4
└── docs/               # Additional documentation
    └── CHAT_framework.md
```

## Technical Components

### 1. CHAT Framework Implementation (`agent.py`)

#### Learning Levels
```python
LEARNING_LEVELS = {
    "novice": {
        "complexity": 1,
        "explanation_depth": "basic",
        "terminology": "simple"
    },
    "beginner": {
        "complexity": 2,
        "explanation_depth": "expanded",
        "terminology": "introducing specialized terms"
    },
    # ... additional levels
}
```

#### Cultural Contexts
```python
CULTURAL_CONTEXTS = {
    "east_african": {
        "regions": ["Kenya", "Tanzania", "Uganda"],
        "terminology": {
            "game": "Bano",
            "marbles": "dende"
        }
    }
    # ... additional contexts
}
```

### 2. Memory Management (`auth.py`)

```python
def setup_memory():
    """Initialize conversation memory"""
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))

def restore_memory(thread: ThreadDict):
    """Restore conversation from thread history"""
    # Implementation details...
```

### 3. Quiz System (`main.py`)

#### Quiz Question Structure
```python
{
    "category": "rules",
    "question": "What is typically used as game pieces in Bano?",
    "options": ["Dice", "Marbles or bottle caps", "Playing cards", "Sticks"],
    "correct": 1,
    "level": "novice",
    "activity_component": "tools"
}
```

### 4. Adaptive Content Delivery

The system adapts content based on:
- **User Knowledge Level**: Assessed through conversation analysis
- **Cultural Context**: Determined by regional mentions
- **Learning Progress**: Tracked through quiz performance and concept exploration

## API References

### Core Functions

#### `setup_runnable() -> Runnable`
Initializes the main conversation chain with CHAT framework integration.

**Returns**: Configured LangChain runnable

#### `assess_user_knowledge(conversation_history, topic) -> str`
Analyzes conversation to determine user's knowledge level.

**Parameters**:
- `conversation_history`: List of conversation messages
- `topic`: Current conversation topic

**Returns**: Learning level ("novice", "beginner", "intermediate", "advanced")

#### `adapt_content_to_level(content: str, user_level: str) -> str`
Modifies content based on user's learning level.

**Parameters**:
- `content`: Original content to adapt
- `user_level`: User's current learning level

**Returns**: Adapted content string

### Chainlit Callbacks

#### `@cl.on_chat_start`
Initializes new chat session with user profile and media assets.

#### `@cl.on_message`
Handles incoming messages with CHAT framework processing.

#### `@cl.action_callback("quiz_request")`
Processes quiz requests with adaptive difficulty.

## Development

### Adding New Features

1. **New Cultural Context**:
   ```python
   CULTURAL_CONTEXTS["new_region"] = {
       "regions": ["Country1", "Country2"],
       "terminology": {...},
       "cultural_significance": "...",
       "historical_context": "..."
   }
   ```

2. **New Quiz Categories**:
   ```python
   QUIZ_QUESTIONS.append({
       "category": "new_category",
       "question": "Your question here",
       "options": ["A", "B", "C", "D"],
       "correct": 0,
       "level": "beginner",
       "activity_component": "rules"
   })
   ```

### Testing

```bash
# Run basic functionality test
python -m pytest tests/

# Test specific components
python -m pytest tests/test_agent.py
python -m pytest tests/test_quiz.py
```

### Code Style

The project follows PEP 8 guidelines with:
- Line length: 100 characters
- Indentation: 4 spaces
- Docstring format: Google style

## Troubleshooting

### Common Issues

1. **Media Files Not Loading**
   ```
   Error: FileNotFoundError: [Errno 2] No such file or directory
   ```
   **Solution**: Ensure all media files are in the correct directory with exact filenames.

2. **API Key Errors**
   ```
   Error: Invalid API key for Cohere/SerpAPI
   ```
   **Solution**: Verify API keys in `.env` file and check key validity.

3. **Memory Issues**
   ```
   Error: NoneType object has no attribute 'chat_memory'
   ```
   **Solution**: Ensure `setup_memory()` is called before message processing.

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

- **Memory Management**: Implement conversation pruning for long sessions
- **Caching**: Cache frequently accessed cultural context data
- **Async Processing**: Use async/await for API calls

## Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test thoroughly
4. Commit changes: `git commit -m "Add new feature"`
5. Push to branch: `git push origin feature/new-feature`
6. Create Pull Request

### Contribution Guidelines

- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation for API changes
- Ensure CHAT framework principles are maintained

### Areas for Contribution

- **New Cultural Contexts**: Add support for additional African regions
- **Enhanced Quiz System**: More sophisticated question generation
- **Advanced Analytics**: User learning progress visualization
- **Accessibility**: Screen reader support and keyboard navigation
- **Mobile Optimization**: Responsive design improvements

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- **CHAT Framework**: Based on Cultural-Historical Activity Theory by Vygotsky
- **Bano Game**: Traditional African game - cultural heritage preservation
- **Community**: Thanks to all contributors and cultural consultants

## Support

For technical support or questions:
- Create an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## Changelog

### Version 1.0.0
- Initial release with CHAT framework
- Multi-regional cultural support
- Interactive quiz system
- Multimedia educational content
- Adaptive learning progression

---

*Last Updated: July 2025*
