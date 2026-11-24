WITH versions AS (
    SELECT DISTINCT event, order_id, kind, currency, cents FROM raw_events
),
ambiguous AS (
    SELECT event FROM versions GROUP BY event HAVING COUNT(*) > 1
),
blocked AS (
    SELECT DISTINCT order_id, currency FROM versions JOIN ambiguous USING (event)
),
ledger AS (
    SELECT order_id, currency, SUM(CASE kind WHEN 'refund' THEN -cents ELSE cents END) AS expected
    FROM versions
    WHERE event NOT IN (SELECT event FROM ambiguous)
    GROUP BY order_id, currency
),
keys AS (
    SELECT order_id, currency FROM ledger
    UNION SELECT order_id, currency FROM settlements
    UNION SELECT order_id, currency FROM blocked
)
SELECT k.order_id, k.currency, l.expected AS event_net, s.cents AS settled,
       CASE WHEN b.order_id IS NULL AND l.expected IS NOT NULL AND s.cents IS NOT NULL
            THEN s.cents - l.expected END AS delta_cents,
       CASE WHEN b.order_id IS NOT NULL THEN 'conflicting event'
            WHEN l.order_id IS NULL THEN 'settlement only'
            WHEN s.order_id IS NULL THEN 'missing settlement'
            WHEN l.expected <> s.cents THEN 'amount mismatch'
            ELSE 'matched' END AS status
FROM keys k
LEFT JOIN ledger l USING (order_id, currency)
LEFT JOIN settlements s USING (order_id, currency)
LEFT JOIN blocked b USING (order_id, currency)
ORDER BY k.order_id, k.currency;
