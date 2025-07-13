import asyncio
import logging
from typing import Annotated
from pydantic import BaseModel, Field
import httpx
import os

from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import deepgram, cartesia, google, silero
from dotenv import load_dotenv

load_dotenv()

# Frontend API configuration
FRONTEND_API_URL = os.getenv("FRONTEND_API_URL", "http://localhost:3000/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for input validation - simplified for Google Gemini compatibility
class CartItem(BaseModel):
    quantity: int
    item_name: str

# FastAPI POST request functions for frontend communication
async def grocery_api_add_item(item_name: str, quantity: int) -> dict:
    """FastAPI POST request to add item to cart with smart name normalization"""
    logger.info(f"🛒 API CALL: Adding {quantity} {item_name} to cart")
    try:
        # Normalize item name (lowercase, handle common plurals)
        normalized_name = item_name.lower().strip()
        if normalized_name.endswith('s') and len(normalized_name) > 1:
            # For most cases, keep the plural form for consistency
            final_name = normalized_name
        else:
            # Add 's' for singular items to make them plural
            final_name = normalized_name + 's' if not normalized_name.endswith('s') else normalized_name
        
        logger.info(f"📝 Normalized '{item_name}' -> '{final_name}'")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "item_name": final_name,
                "quantity": quantity,
                "action": "add"
            }
            response = await client.post(
                f"{FRONTEND_API_URL}/cart/add",
                json=payload,
                timeout=10.0
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"🛒 API SUCCESS: {result}")
                return result
            else:
                error_result = {
                    "success": False,
                    "message": f"Failed to add {item_name} to cart. Status: {response.status_code}"
                }
                logger.error(f"🛒 API ERROR: {error_result}")
                return error_result
    except Exception as e:
        error_result = {"success": False, "message": f"Error adding item to cart: {str(e)}"}
        logger.error(f"🛒 API EXCEPTION: {error_result}")
        return error_result

async def grocery_api_remove_item(item_name: str, quantity: int) -> dict:
    """FastAPI POST request to remove item from cart with smart name matching"""
    logger.info(f"🗑️ API CALL: Removing {quantity} {item_name} from cart")
    try:
        async with httpx.AsyncClient() as client:
            # First, try the exact name
            payload = {
                "item_name": item_name,
                "quantity": quantity,
                "action": "remove"
            }
            response = await client.post(
                f"{FRONTEND_API_URL}/cart/remove",
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    logger.info(f"🗑️ API SUCCESS: {result}")
                    return result
                else:
                    # If exact name failed, try smart matching
                    logger.info(f"🔍 Exact name '{item_name}' failed, trying smart matching...")
                    
                    # Get current cart to see what's available
                    cart_response = await client.get(f"{FRONTEND_API_URL}/cart/view", timeout=10.0)
                    if cart_response.status_code == 200:
                        cart_data = cart_response.json()
                        cart_items = cart_data.get("cart_items", [])
                        
                        # Try to find a match (case-insensitive, singular/plural)
                        item_lower = item_name.lower().strip()
                        for cart_item in cart_items:
                            cart_item_name = cart_item["item"].lower().strip()
                            
                            # Check various matching patterns
                            if (item_lower == cart_item_name or
                                item_lower + "s" == cart_item_name or
                                item_lower == cart_item_name + "s" or
                                item_lower.rstrip("s") == cart_item_name.rstrip("s")):
                                
                                logger.info(f"🎯 Found match: '{item_name}' -> '{cart_item['item']}'")
                                # Try with the matched name
                                new_payload = {
                                    "item_name": cart_item["item"],
                                    "quantity": quantity,
                                    "action": "remove"
                                }
                                retry_response = await client.post(
                                    f"{FRONTEND_API_URL}/cart/remove",
                                    json=new_payload,
                                    timeout=10.0
                                )
                                if retry_response.status_code == 200:
                                    retry_result = retry_response.json()
                                    logger.info(f"🗑️ API SUCCESS (matched): {retry_result}")
                                    return retry_result
                    
                    # If no match found, return the original result
                    logger.warning(f"🗑️ No matching items found for '{item_name}'")
                    return result
            else:
                error_result = {
                    "success": False,
                    "message": f"Failed to remove {item_name} from cart. Status: {response.status_code}"
                }
                logger.error(f"🗑️ API ERROR: {error_result}")
                return error_result
    except Exception as e:
        error_result = {"success": False, "message": f"Error removing item from cart: {str(e)}"}
        logger.error(f"🗑️ API EXCEPTION: {error_result}")
        return error_result

RunContext_T = RunContext

class GroceryAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are a friendly and helpful grocery shopping assistant. You help users manage their shopping cart by adding or removing items. Always be polite, conversational, and confirm actions clearly.

            IMPORTANT: When users ask to add or remove items, you MUST use the appropriate tools available to you.

            Available tools (YOU MUST USE THESE):
            - add_to_cart: Use when users want to add items to their cart
            - remove_from_cart: Use when users want to remove items from their cart

            Examples of requests that REQUIRE add_to_cart tool:
            - "Add 5 apples" / "I need 2 bananas" / "Put 3 oranges in my cart"
            - "Can you add some bread?" / "Add milk" / "I want 10 eggs"

            Examples of requests that REQUIRE remove_from_cart tool:
            - "Remove milk from my cart" / "Take out the bananas"
            - "Delete 2 apples" / "Remove bread"

            ALWAYS extract the quantity and item name clearly. If quantity is not specified, assume 1.
            ALWAYS use the tools - do not just respond with text when items need to be added or removed.
            Be conversational and helpful. Ask if they need anything else after completing actions.""",
            llm=google.LLM(model="gemini-2.5-flash", temperature=0.3),
            tts=cartesia.TTS(
                model="sonic-2",
                voice="79a125e8-cd45-4c13-8a67-188112f4dd22",
                speed=1.0
            )
        )
        logger.info("🤖 GroceryAgent initialized with voice API")

    async def on_enter(self):
        """Agent is ready"""
        logger.info("🚪 Agent entering - ready for voice commands")
        logger.info("✅ Agent ready - say 'add 3 apples' or 'remove 2 bananas'")

    @function_tool()
    async def add_to_cart(
        self, 
        quantity: Annotated[int, "Number of items to add (must be positive)"],
        item_name: Annotated[str, "Name of the grocery item to add"],
        context: RunContext_T
    ) -> str:
        """Add items to the grocery cart."""
        logger.info(f"🔧 TOOL CALLED: add_to_cart(quantity={quantity}, item_name='{item_name}')")
        try:
            # Manual validation for Google Gemini compatibility
            if quantity < 1:
                raise ValueError("Quantity must be positive")
            if not item_name or len(item_name.strip()) == 0:
                raise ValueError("Item name cannot be empty")
            
            cart_item = CartItem(quantity=quantity, item_name=item_name.strip())
            logger.info(f"✅ Validation successful: {cart_item}")
            result = await grocery_api_add_item(cart_item.item_name, cart_item.quantity)
            if result["success"]:
                response = f"Perfect! I've successfully added {cart_item.quantity} {cart_item.item_name} to your cart. Is there anything else you'd like to add?"
                logger.info(f"✅ Tool response: {response}")
                return response
            else:
                response = f"I'm sorry, I couldn't add {cart_item.item_name} to your cart. Please try again."
                logger.warning(f"⚠️ Tool response (failed): {response}")
                return response
        except Exception as e:
            logger.error(f"❌ Error in add_to_cart: {e}")
            error_response = f"Sorry, there was an error processing your request: {str(e)}"
            return error_response

    @function_tool()
    async def remove_from_cart(
        self, 
        quantity: Annotated[int, "Number of items to remove (must be positive)"],
        item_name: Annotated[str, "Name of the grocery item to remove"],
        context: RunContext_T
    ) -> str:
        """Remove items from the grocery cart."""
        logger.info(f"🔧 TOOL CALLED: remove_from_cart(quantity={quantity}, item_name='{item_name}')")
        try:
            # Manual validation for Google Gemini compatibility
            if quantity < 1:
                raise ValueError("Quantity must be positive")
            if not item_name or len(item_name.strip()) == 0:
                raise ValueError("Item name cannot be empty")
                
            cart_item = CartItem(quantity=quantity, item_name=item_name.strip())
            logger.info(f"✅ Validation successful: {cart_item}")
            result = await grocery_api_remove_item(cart_item.item_name, cart_item.quantity)
            if result["success"]:
                response = f"Done! I've successfully removed {cart_item.quantity} {cart_item.item_name} from your cart. Anything else you'd like me to help with?"
                logger.info(f"✅ Tool response: {response}")
                return response
            else:
                response = f"I'm sorry, I couldn't remove {cart_item.item_name} from your cart. Please try again."
                logger.warning(f"⚠️ Tool response (failed): {response}")
                return response
        except Exception as e:
            logger.error(f"❌ Error in remove_from_cart: {e}")
            error_response = f"Sorry, there was an error processing your request: {str(e)}"
            return error_response

async def entrypoint(ctx: JobContext):
    """Main entrypoint using the working voice API pattern from restaurant agent"""
    await ctx.connect()
    logger.info("🔗 Connected to LiveKit room")

    # Create session using the same pattern as restaurant agent
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en-US",
            interim_results=True,
            smart_format=True,
            punctuate=True
        ),
        llm=google.LLM(model="gemini-2.0-flash-lite", temperature=0.3),
        tts=cartesia.TTS(
            model="sonic-2",
            voice="79a125e8-cd45-4c13-8a67-188112f4dd22",
            speed=1.0
        ),
        vad=silero.VAD.load(),
    )
    
    # Add event handlers for debugging
    @session.on("user_speech_committed")
    def on_speech(event):
        logger.info(f"🎤 Voice input: '{event.transcript}'")
        
    @session.on("agent_response_committed")
    def on_response(event):
        logger.info("🗣️ Agent responded via voice")

    # Create and start agent
    agent = GroceryAgent()
    
    await session.start(agent=agent, room=ctx.room)
    logger.info("✅ Grocery voice agent ready!")
    
    print("\n" + "="*60)
    print("     🛒 GROCERY SHOPPING VOICE ASSISTANT")
    print("="*60)
    print("Ready! Use voice commands like:")
    print("  • 'Add 3 apples'")
    print("  • 'Remove 2 bananas'") 
    print("  • 'Add milk to my cart'")
    print("  • 'Remove bread'")
    print("\nFor text mode: Press [Ctrl+B] then type")
    print("Press [Q] to quit")
    print("="*60)

if __name__ == "__main__":
    # Check environment variables
    required_vars = ["DEEPGRAM_API_KEY", "GOOGLE_API_KEY", "CARTESIA_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        exit(1)
    else:
        logger.info("✅ All required environment variables are set")
        
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
