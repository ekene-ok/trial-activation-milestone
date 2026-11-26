-- Who reaches the first invoice by day 3, by sign-up device, team size and source.
CREATE OR REPLACE TABLE invoice_by_day3_segments AS
SELECT 'Device' AS cut, signup_device AS segment, COUNT(*) AS trials,
       ROUND(AVG(COALESCE(day_send_invoice <= 3, FALSE)::INT), 3) AS share_invoice_by_day3
FROM trial_view GROUP BY 1, 2
UNION ALL
SELECT 'Team size', team_size, COUNT(*), ROUND(AVG(COALESCE(day_send_invoice <= 3, FALSE)::INT), 3) FROM trial_view GROUP BY 1, 2
UNION ALL
SELECT 'Source', signup_source, COUNT(*), ROUND(AVG(COALESCE(day_send_invoice <= 3, FALSE)::INT), 3) FROM trial_view GROUP BY 1, 2
ORDER BY cut, share_invoice_by_day3;
