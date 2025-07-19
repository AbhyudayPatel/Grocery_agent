# 🛒 Grocery Shopping Voice Agent [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/AbhyudayPatel/Grocery_Voice_Agent)

A voice-powered grocery shopping assistant that allows users to manage their shopping cart through natural voice commands. The agent uses LiveKit for real-time voice processing and integrates with a FastAPI backend to maintain cart state.

## 🌟 Features

- **Voice Commands**: Add or remove items using natural speech
- **Smart Item Matching**: Handles singular/plural forms and common variations
- **Real-time Cart Management**: Persistent cart state during the session
- **Multi-modal Input**: Supports both voice and text input
- **RESTful API**: Complete backend API for cart operations
- **Cross-platform**: Works on Windows, macOS, and Linux

## 🏗️ Project Structure

```
Grocery_agent/
├── dummy_frontend_api.py    # FastAPI backend for cart management
├── voice_agent_working.py   # Voice agent with LiveKit integration
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables (API keys)
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- API keys for:
  - [Deepgram](https://deepgram.com/) (Speech-to-Text)
  - [Cartesia](https://cartesia.ai/) (Text-to-Speech)
  - [Google AI](https://ai.google.dev/) (LLM)

### 2. Installation

1. **Clone or download the project:**
   ```powershell
   cd "c:\Users\Abhyuday Patel\Desktop\Grocery_agent"
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   
   Edit the `.env` file and add your API keys:
   ```properties
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   CARTESIA_API_KEY=your_cartesia_api_key_here
   GOOGLE_API_KEY=your_google_ai_api_key_here
   FRONTEND_API_URL=http://localhost:3000/api
   ```

### 3. Running the Application

**⚠️ Important: Start the backend first, then the voice agent!**

#### Step 1: Start the Backend API
```powershell
python dummy_frontend_api.py
```

The API will start on `http://localhost:3000` and provide these endpoints:
- `GET /` - Health check
- `POST /api/cart/add` - Add items to cart
- `POST /api/cart/remove` - Remove items from cart
- `GET /api/cart/view` - View cart contents
- `DELETE /api/cart/clear` - Clear cart

#### Step 2: Start the Voice Agent
In a new terminal window:
```powershell
python voice_agent_working.py console
```

## 🎯 Usage Examples

Once both services are running, you can use voice commands like:

### Adding Items
- "Add 3 apples"
- "I need 2 bananas"
- "Put 5 oranges in my cart"
- "Add milk"
- "Can you add some bread?"

### Removing Items
- "Remove milk from my cart"
- "Take out the bananas"
- "Delete 2 apples"
- "Remove bread"

### Text Mode
- Press `[Ctrl+B]` to switch to text input mode
- Type your commands instead of speaking
- Press `[Q]` to quit the application

## 🔧 API Reference

### Cart Operations

#### Add Item to Cart
```http
POST /api/cart/add
Content-Type: application/json

{
  "item_name": "apples",
  "quantity": 3,
  "action": "add"
}
```

#### Remove Item from Cart
```http
POST /api/cart/remove
Content-Type: application/json

{
  "item_name": "apples",
  "quantity": 2,
  "action": "remove"
}
```

#### View Cart
```http
GET /api/cart/view
```

#### Clear Cart
```http
DELETE /api/cart/clear
```

### Response Format
```json
{
  "success": true,
  "message": "Successfully added 3 apples to cart",
  "cart_items": [
    {"item": "apples", "quantity": 3}
  ],
  "total_items": 3
}
```

## 🛠️ Technical Details

### Voice Agent Features
- **Speech-to-Text**: Deepgram Nova-2 model with real-time transcription
- **Text-to-Speech**: Cartesia Sonic-2 model with natural voice synthesis
- **LLM**: Google Gemini 2.0 Flash Lite for intelligent conversation
- **Voice Activity Detection**: Silero VAD for speech detection
- **Smart Matching**: Handles plural/singular variations automatically

### Backend Features
- **FastAPI**: Modern, fast web framework with automatic API docs
- **CORS Support**: Enabled for frontend integration
- **Request Validation**: Pydantic models for data validation
- **Comprehensive Logging**: Detailed logging for debugging
- **Error Handling**: Robust error handling with meaningful messages

## 🔍 Troubleshooting

### Common Issues

1. **"ModuleNotFoundError" when starting**
   ```powershell
   pip install -r requirements.txt
   ```

2. **"Missing API key" errors**
   - Check that all API keys are set in `.env`
   - Ensure `.env` file is in the project root directory

3. **Voice agent can't connect to API**
   - Make sure `dummy_frontend_api.py` is running first
   - Check that port 3000 is not blocked by firewall

4. **No audio input/output**
   - Check microphone permissions
   - Ensure speakers/headphones are connected
   - Try switching to text mode with `[Ctrl+B]`


**Happy Shopping! 🛒✨**
