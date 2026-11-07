RETURN_QUERY = """
    SELECT
        r.id::text            AS return_id,
        r.order_id::text      AS order_id,
        r.user_id::text       AS customer_id,
        COALESCE(
            (
                SELECT JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'id', rp.id::text,
                        'object_key', rp.object_key,
                        'content_type', rp.content_type,
                        'bytes', rp.bytes
                    ) ORDER BY rp.id
                )
                FROM return_photos rp
                WHERE rp.return_id = r.id
            ),
            '[]'::json
        )                     AS photos,

        -- Customer history (prior returns only; excludes this one)
        (
            SELECT JSON_BUILD_OBJECT(
                'orders',   (SELECT count(*) FROM orders o WHERE o.user_id = r.user_id),
                'returns',  count(*),
                'denied',   count(*) FILTER (WHERE h.final_decision = 'deny'),
                'approved', count(*) FILTER (WHERE h.final_decision = 'approve')
            )
            FROM returns h
            WHERE h.user_id = r.user_id
              AND h.id <> r.id
        )                     AS customer_history,

        r.created_at,
        o.delivered_at,
        r.reason_code,
        r.reason_text,
        r.amount,
        r.status,
        oi.id::text           AS order_item_id,
        oi.product_id::text   AS product_id,
        oi.quantity,
        oi.price_at_purchase,
        oi.name_at_purchase,
        p.name                AS product_name,
        p.description         AS product_description,
        p.category            AS product_category,
        p.price               AS current_product_price,
        p.image_key           AS product_image_key
    FROM returns r
    JOIN orders o
        ON o.id = r.order_id
    JOIN order_items oi
        ON oi.id = r.order_item_id
       AND oi.order_id = r.order_id
    LEFT JOIN products p
        ON p.id = oi.product_id
    WHERE r.id = %(return_id)s::uuid
"""