WITH purchase_days AS (
    SELECT customer, day, SUM(spend) AS revenue
    FROM orders
    GROUP BY customer, day
),
history AS (
    SELECT customer,
           julianday(:cutoff) - julianday(MAX(day)) AS days_since_order,
           julianday(:cutoff) - julianday(MIN(day)) AS age_days,
           COUNT(*) AS shopping_days,
           AVG(revenue) AS mean_daily_basket,
           SUM(day >= date(:cutoff, '-60 days')) AS active_days_60
    FROM purchase_days
    WHERE day < :cutoff
    GROUP BY customer
),
future AS (
    SELECT DISTINCT customer
    FROM purchase_days
    WHERE day >= :cutoff AND day < date(:cutoff, '+90 days')
)
SELECT h.*, CAST(f.customer IS NOT NULL AS INTEGER) AS bought_in_90_days
FROM history AS h LEFT JOIN future AS f USING (customer)
ORDER BY customer;
