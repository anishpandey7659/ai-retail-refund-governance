RETURN_REVIEW_UPDATE_QUERY = """
    UPDATE returns
    SET ai_result = %(ai_result)s, status = %(status)s
    WHERE id = %(return_id)s::uuid
    RETURNING id
"""


RETURN_QUERY = """
    SELECT
        r.id::text            AS return_id,
        r.order_id            AS order_id,
        r.user_id::text       AS customer_id,
        u.email               AS customer_email,
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

        -- Customer history JSON: orders + returns counts (prior only; excludes this one)
        JSON_BUILD_OBJECT(
            'orders',  hist.orders_count,
            'returns', hist.returns_count
        )                     AS customer_history,

        -- Exposed as separate top-level columns so build_case() can read them directly
        hist.approved_count   AS approved,
        hist.denied_count     AS denied,

        r.created_at,
        o.delivered_at,
        r.reason_code,
        r.reason_text,
        r.amount,
        r.status,
        oi.id                 AS order_item_id,
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
    JOIN users u
        ON u.id = r.user_id
    JOIN orders o
        ON o.id = r.order_id
    JOIN order_items oi
        ON oi.id = r.order_item_id
       AND oi.order_id = r.order_id
    LEFT JOIN products p
        ON p.id = oi.product_id
    -- Single lateral scan replaces three separate correlated subqueries
    CROSS JOIN LATERAL (
        SELECT
            (
                SELECT count(*)
                FROM orders o2
                WHERE o2.user_id = r.user_id
            )                                               AS orders_count,
            count(*)                                        AS returns_count,
            count(*) FILTER (WHERE h.status = 'approved')  AS approved_count,
            count(*) FILTER (WHERE h.status = 'denied')    AS denied_count
        FROM returns h
        WHERE h.user_id = r.user_id
          AND h.id <> r.id
    ) AS hist
    WHERE r.id = %(return_id)s::uuid
"""


ML_CONTEXT_QUERY = """
    WITH target AS (
        SELECT
            r.id AS return_id,
            r.user_id,
            r.order_id,
            r.created_at AS return_created_at,
            r.amount,
            r.reason_code,
            r.item_opened,
            o.created_at AS order_created_at,
            o.delivered_at,
            o.payment_method_fingerprint AS order_payment_fingerprint
        FROM returns r
        JOIN orders o ON o.id = r.order_id
        WHERE r.id = %(return_id)s::uuid
    )
    SELECT
        CASE
            WHEN history.item_count > 0
            THEN round(
                100.0 * history.returned_item_count / history.item_count,
                2
            )
            ELSE NULL
        END AS return_rate_pct,
        support.contact_count AS customer_support_contacts,
        CASE
            WHEN history.order_total > 0
            THEN round(
                COALESCE(history.refund_total, 0) / history.order_total,
                4
            )
            ELSE NULL
        END AS refund_to_order_ratio,
        appeals.previous_dispute_count,
        target.item_opened AS item_returned_opened,
        fingerprints.multiple_accounts_flag,
        CASE
            WHEN target.order_payment_fingerprint IS NULL
              OR refund.destination_fingerprint IS NULL
            THEN NULL
            ELSE target.order_payment_fingerprint
                 <> refund.destination_fingerprint
        END AS refund_to_different_account,
        target.amount AS refund_amount_requested_usd,
        target.reason_code AS return_reason,
        CASE
            WHEN target.delivered_at IS NULL THEN NULL
            ELSE EXISTS (
                SELECT 1
                FROM order_address_changes ac
                WHERE ac.order_id = target.order_id
                  AND ac.changed_at >= target.order_created_at
                  AND ac.changed_at <= target.delivered_at
            )
        END AS address_change_before_delivery
    FROM target
    CROSS JOIN LATERAL (
        SELECT
            (
                SELECT count(*)
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                WHERE o.user_id = target.user_id
                  AND o.created_at < target.order_created_at
            ) AS item_count,
            (
                SELECT count(DISTINCT h.order_item_id)
                FROM returns h
                JOIN orders ho ON ho.id = h.order_id
                WHERE h.user_id = target.user_id
                  AND ho.created_at < target.order_created_at
            ) AS returned_item_count,
            (
                SELECT COALESCE(sum(o.total_amount), 0)
                FROM orders o
                WHERE o.user_id = target.user_id
                  AND o.created_at < target.order_created_at
            ) AS order_total,
            (
                SELECT COALESCE(sum(rf.amount), 0)
                FROM return_refunds rf
                JOIN returns hr ON hr.id = rf.return_id
                JOIN orders ho ON ho.id = hr.order_id
                WHERE hr.user_id = target.user_id
                  AND hr.created_at < target.return_created_at
                  AND ho.created_at < target.order_created_at
                  AND rf.status = 'succeeded'
                  AND rf.processed_at <= target.return_created_at
            ) AS refund_total
    ) AS history
    CROSS JOIN LATERAL (
        SELECT count(*)::integer AS contact_count
        FROM support_contacts sc
        WHERE sc.user_id = target.user_id
          AND sc.contacted_at < target.return_created_at
    ) AS support
    CROSS JOIN LATERAL (
        SELECT count(*)::integer AS previous_dispute_count
        FROM returns h
        WHERE h.user_id = target.user_id
          AND h.created_at < target.return_created_at
          AND h.status IN ('denied', 'escalated')
    ) AS appeals
    CROSS JOIN LATERAL (
        SELECT CASE
            WHEN NOT EXISTS (SELECT 1 FROM fingerprints WHERE user_id = target.user_id) THEN NULL
            ELSE EXISTS (
                SELECT 1
                FROM fingerprints own
                JOIN fingerprints other
                  ON other.fingerprint_type = own.fingerprint_type
                 AND other.fingerprint_hash = own.fingerprint_hash
                 AND other.user_id <> target.user_id
                WHERE own.user_id = target.user_id
            )
        END AS multiple_accounts_flag
    ) AS fingerprints
    LEFT JOIN LATERAL (
        SELECT rf.destination_fingerprint
        FROM return_refunds rf
        WHERE rf.return_id = target.return_id
          AND rf.created_at <= target.return_created_at
          AND rf.destination_fingerprint IS NOT NULL
        ORDER BY rf.created_at DESC
        LIMIT 1
    ) AS refund ON TRUE
"""
