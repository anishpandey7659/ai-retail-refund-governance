from worker.pipeline.nodes.base import Case

raw = {
    "case_id": "e23f609f-8a52-43c1-8364-4c6832e8ced0",
    "order_id": 1,
    "customer_id": "79fbb472-77f2-4b66-af71-0be978b2a4ed",
    "return_request_at": "2026-11-03T07:25:16.864711+00:00",
    "item_name": "Speaker",
    "reason_code": "defective",
    "description": (
        "The JBL speaker is defective because it is not functioning properly. "
        "The sound is distorted and intermittently cuts off, even at normal "
        "volume levels."
    ),
    "photos": [
        {
            "id": "43b7e5ee-0b86-41e7-9b18-23c44ca590f0",
            "object_key": (
                "returns/e23f609f-8a52-43c1-8364-4c6832e8ced0/"
                "1d285446e0784ceca1e7cd217eb4459e.jpg"
            ),
            "content_type": "image/jpeg",
            "bytes": 345738,
        }
    ],
    "customer_history": {
        "orders": 1,
        "returns": 0,
        "approved": 0,
        "denied": 0,
        "return_rate": 0.0,
    },
    "product_info": {
        "product_id": "1cbe5fdf-328a-48ea-a967-2d09733c0e13",
        "title": "Speaker",
        "description": (
            "Portable Bluetooth speaker with clear sound, built-in microphone "
            "and 12-hour playtime."
        ),
        "category": "electronics",
        "current_price": 34.99,
        "image_key": "products/RG-007.jpg",
    },
    "order_info": {
        "order_item_id": 2,
        "quantity": 1,
        "price_at_purchase": 34.99,
        "return_amount": 34.99,
        "delivered_at": "2026-10-23T15:00:20.665706+00:00",
    },
    "status": "pending",
    "gate_result": None,
    "agent_results": {},
}

case = Case.model_validate(raw)
