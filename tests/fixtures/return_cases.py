from worker.pipeline.nodes.base import Case


def make_case(scenario: str) -> Case:
    if scenario not in {
        "low_risk",
        "high_risk",
        "suspicious",
        "defective_product",
    }:
        raise ValueError(f"Unknown return fixture scenario: {scenario}")

    reason_code = "defective" if scenario == "defective_product" else "no_longer_needed"
    if scenario == "suspicious":
        reason_code = "wrong_item"

    photos = []
    if scenario in {"suspicious", "defective_product"}:
        photos = [
            {
                "id": f"photo-{scenario}",
                "object_key": f"returns/{scenario}.jpg",
                "content_type": "image/jpeg",
                "bytes": 1024,
            }
        ]

    return Case.model_validate(
        {
            "case_id": f"case-{scenario}",
            "order_id": 1,
            "customer_id": "customer-test",
            "return_request_at": "2026-11-01T10:00:00+00:00",
            "item_name": "Bluetooth Speaker",
            "reason_code": reason_code,
            "description": (
                "The speaker intermittently loses sound at normal volume."
                if scenario == "defective_product"
                else "The item is being returned in its original condition."
            ),
            "photos": photos,
            "customer_history": {
                "orders": 8,
                "returns": 4 if scenario == "high_risk" else 1,
                "approved": 1,
                "denied": 1 if scenario == "high_risk" else 0,
                "return_rate": 0.5 if scenario == "high_risk" else 0.05,
            },
            "product_info": {
                "product_id": "product-test",
                "title": "Bluetooth Speaker",
                "description": "Portable Bluetooth speaker with a 12-hour battery.",
                "category": "electronics",
                "current_price": 49.99,
                "image_key": "products/speaker.jpg",
            },
            "order_info": {
                "order_item_id": 1,
                "quantity": 1,
                "price_at_purchase": 49.99,
                "return_amount": 49.99,
                "delivered_at": "2026-10-25T10:00:00+00:00",
            },
        }
    )
