from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dummy Grocery Cart API", version="1.0.0")

# Pydantic models for request validation
class CartItemRequest(BaseModel):
    item_name: str
    quantity: int
    action: str  # "add" or "remove"

class CartResponse(BaseModel):
    success: bool
    message: str
    cart_items: List[Dict] = []
    total_items: int = 0

# In-memory cart storage (for demo purposes)
cart_storage: Dict[str, int] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Dummy Grocery Cart API is running!",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/cart/add",
            "/api/cart/remove",
            "/api/cart/view",
            "/api/cart/clear"
        ]
    }

@app.post("/api/cart/add", response_model=CartResponse)
async def add_to_cart(request: CartItemRequest):
    """Add items to the cart"""
    try:
        logger.info(f"🛒 Received ADD request: {request.dict()}")
        
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        item_name = request.item_name.lower().strip()
        
        # Add to cart
        if item_name in cart_storage:
            cart_storage[item_name] += request.quantity
        else:
            cart_storage[item_name] = request.quantity
        
        # Prepare response
        cart_items = [{"item": item, "quantity": qty} for item, qty in cart_storage.items()]
        total_items = sum(cart_storage.values())
        
        response = CartResponse(
            success=True,
            message=f"Successfully added {request.quantity} {request.item_name} to cart",
            cart_items=cart_items,
            total_items=total_items
        )
        
        logger.info(f"✅ ADD successful: {response.dict()}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding to cart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/cart/remove", response_model=CartResponse)
async def remove_from_cart(request: CartItemRequest):
    """Remove items from the cart"""
    try:
        logger.info(f"🗑️ Received REMOVE request: {request.dict()}")
        
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        item_name = request.item_name.lower().strip()
        
        # Check if item exists in cart
        if item_name not in cart_storage:
            response = CartResponse(
                success=False,
                message=f"{request.item_name} is not in your cart",
                cart_items=[{"item": item, "quantity": qty} for item, qty in cart_storage.items()],
                total_items=sum(cart_storage.values())
            )
            logger.warning(f"⚠️ Item not found: {response.dict()}")
            return response
        
        # Remove from cart
        if cart_storage[item_name] <= request.quantity:
            # Remove completely if quantity to remove >= current quantity
            removed_qty = cart_storage[item_name]
            del cart_storage[item_name]
            message = f"Removed all {removed_qty} {request.item_name} from cart"
        else:
            # Reduce quantity
            cart_storage[item_name] -= request.quantity
            message = f"Removed {request.quantity} {request.item_name} from cart"
        
        # Prepare response
        cart_items = [{"item": item, "quantity": qty} for item, qty in cart_storage.items()]
        total_items = sum(cart_storage.values())
        
        response = CartResponse(
            success=True,
            message=message,
            cart_items=cart_items,
            total_items=total_items
        )
        
        logger.info(f"✅ REMOVE successful: {response.dict()}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error removing from cart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/cart/view", response_model=CartResponse)
async def view_cart():
    """View current cart contents"""
    try:
        cart_items = [{"item": item, "quantity": qty} for item, qty in cart_storage.items()]
        total_items = sum(cart_storage.values())
        
        response = CartResponse(
            success=True,
            message=f"Cart contains {total_items} items",
            cart_items=cart_items,
            total_items=total_items
        )
        
        logger.info(f"👀 Cart viewed: {len(cart_items)} unique items, {total_items} total")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error viewing cart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/api/cart/clear")
async def clear_cart():
    """Clear all items from cart"""
    try:
        items_cleared = len(cart_storage)
        cart_storage.clear()
        
        logger.info(f"🧹 Cart cleared: {items_cleared} items removed")
        return {
            "success": True,
            "message": f"Cart cleared successfully. Removed {items_cleared} item types.",
            "cart_items": [],
            "total_items": 0
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing cart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Add CORS middleware for frontend integration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    print("🚀 Starting Dummy Grocery Cart API...")
    print("📍 API will be available at: http://localhost:3000")
    print("📋 Endpoints:")
    print("   - GET  /                     (Health check)")
    print("   - POST /api/cart/add         (Add items)")
    print("   - POST /api/cart/remove      (Remove items)")
    print("   - GET  /api/cart/view        (View cart)")
    print("   - DELETE /api/cart/clear     (Clear cart)")
    print("🎯 Voice agent should send requests to: http://localhost:3000/api")
    
    uvicorn.run(
        "dummy_frontend_api:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
