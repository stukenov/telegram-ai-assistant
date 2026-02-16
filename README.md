# Telegram AI Assistant

A multi-functional Telegram bot powered by Large Language Models (LLM) with support for voice messages, weather information, currency exchange rates, and more.

## Features

- **AI-Powered Conversations**: Intelligent chat responses using LLM integration
- **Voice Message Support**: Convert voice messages to text and process them
- **Weather Information**: Get current weather and forecasts for any location
- **Currency Exchange Rates**: Real-time exchange rates from the National Bank of Kazakhstan
- **Document Embedding**: RAG (Retrieval-Augmented Generation) for document-based queries
- **Conversation History**: Maintains context for follow-up questions
- **Multi-Language Support**: Primarily Russian, with automatic language detection

## Project Structure

- `main.py` - Basic bot implementation with weather and exchange rate features
- `sakengptbot2.py` - Advanced bot version with conversation history and voice support
- `audio.py` - Audio transcription service using Whisper model
- `voice.py` - Voice message processing module
- `weather2.py` - Weather information retrieval and formatting
- `rates.py` - Currency exchange rate queries
- `law.py` - Legal document queries (Kazakhstan Labour Code)
- `embed.py` - Document embedding and RAG implementation using LlamaIndex

## Requirements

- Python 3.8+
- Telegram Bot Token (obtain from [@BotFather](https://t.me/BotFather))
- Optional: API keys for additional services (Featherless AI, Geocode)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/stukenov/telegram-ai-assistant.git
cd telegram-ai-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `BOT_TOKEN` - Your Telegram bot token
- `FEATHERLESS_API_KEY` - API key for Featherless AI (optional)
- `GEOCODE_API_KEY` - API key for geocoding service (optional)

## Usage

### Running the basic bot:
```bash
python main.py
```

### Running the advanced bot with conversation history:
```bash
python sakengptbot2.py
```

### Running the audio transcription service:
```bash
python audio.py
```

### Running the document embedding service:
```bash
python embed.py
```

## Bot Commands

- `/start` - Initialize the bot and get a welcome message

## Features in Detail

### Voice Messages
The bot can receive voice messages, transcribe them using Whisper, and process the text as a regular message.

### Weather Queries
Ask about weather in any city:
- "What's the weather in Astana?"
- "Will it rain tomorrow in Dubai?"

### Exchange Rates
Query currency exchange rates:
- "What's the USD exchange rate?"
- "How much is the Euro?"

### Conversation Context
Reply to the bot's previous messages to maintain conversation context and have follow-up discussions.

## Architecture

The bot uses a router-based architecture where incoming messages are classified and routed to specialized handlers:

1. **Router LLM**: Classifies the intent (weather, exchange rate, general query)
2. **Specialized Handlers**: Process specific types of requests
3. **General LLM**: Handles all other conversational queries

## Technologies Used

- **aiogram** - Modern Telegram Bot framework
- **aiohttp** - Async HTTP client/server
- **OpenAI API** - LLM integration via Featherless AI
- **Whisper** - Audio transcription (faster-whisper)
- **LlamaIndex** - Document indexing and RAG
- **pandas** - Data processing
- **httpx** - HTTP client for API requests

## Configuration

### LLM Endpoints
The bot is configured to use custom LLM endpoints. You can modify these in the code or use environment variables to point to your own LLM service.

### Channel Subscription
The bot includes functionality to check if users are subscribed to a specific Telegram channel before allowing access. You can modify or remove this check in the code.

## Development

### Test Files
The project includes several test files for development:
- `test_feather.py` - Test Featherless AI integration
- `test_llm.py` - Test LLM functionality
- `test_metadatallama.py` - Test LlamaIndex metadata
- `test_newbot.py` - Test new bot features
- `test_ollama_embed.py` - Test Ollama embeddings

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created by [@stukenov](https://github.com/stukenov)

## Disclaimer

This bot was created for educational and personal use. Make sure to comply with Telegram's Terms of Service and Bot API guidelines when using this code.
