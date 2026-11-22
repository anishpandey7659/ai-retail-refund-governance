Recommended workflow for your project
1. Create and configure your realm, roles, and clients in the Keycloak UI.
2. Export the realm configuration to infra/keycloak/realm-export.json.
3. Keep the file in your project so you can reproduce the configuration on another machine.


qdrant:   http://localhost:6333/dashboard#/collections

`
[
  {
    "id": "92c2ae68-b55b-4788-a5d5-8bda7c62bfbd",
    "order_id": "11",
    "order_item_id": "10",
    "reason_text": "This bottle was defective place in the first place.",
    "status": "pending",
    "amount": "11.99",
    "ai_proposed_decision": null,
    "final_decision": null,
    "created_at": "2026-10-30T08:49:10.291681Z",
    "photo_urls": [
      "http://localhost:9000/product-images/returns/92c2ae68-b55b-4788-a5d5-8bda7c62bfbd/85be1ab3030c4aca90746d1c5c6a318a.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=localhost%2F20261030%2Fauto%2Fs3%2Faws4_request&X-Amz-Date=20261030T133208Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=1938f2a435048d73cbbe0576f9121c71c0de907484c6fbc7bc39181ec733b6ca"
    ]
  }
]
`

 -F 'order_item_id=12' \
  -F 'reason_code=defective' \
  -F 'reason_text=The speaker stopped producing sound after two days of normal use.' \
  -F 'photo=@Cozy JBL Speaker on Bed.png;type=image/png'