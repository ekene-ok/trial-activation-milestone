-- Conversion by the day of the first invoice.
CREATE OR REPLACE TABLE invoice_timing AS
SELECT
    CASE WHEN day_send_invoice IS NULL THEN 'Never'
         WHEN day_send_invoice <= 1 THEN 'Day 0 to 1'
         WHEN day_send_invoice <= 3 THEN 'Day 2 to 3'
         WHEN day_send_invoice <= 7 THEN 'Day 4 to 7'
         ELSE 'Day 8 to 13' END                     AS first_invoice,
    COUNT(*)                                         AS trials,
    ROUND(AVG(converted_to_paid::INT), 3)            AS conversion_rate
FROM trial_view
GROUP BY 1
ORDER BY CASE first_invoice WHEN 'Day 0 to 1' THEN 1 WHEN 'Day 2 to 3' THEN 2 WHEN 'Day 4 to 7' THEN 3
                            WHEN 'Day 8 to 13' THEN 4 ELSE 5 END;
