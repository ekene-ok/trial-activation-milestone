-- Raw view of each action: how many trials reach it, and conversion with versus without it.
-- Raw gaps overstate each action, because motivated trial users do more of everything.
CREATE OR REPLACE TABLE milestone_raw AS
WITH long AS (
    SELECT 'Add a client' AS action, day_add_client IS NOT NULL AS did, converted_to_paid FROM trial_view
    UNION ALL SELECT 'Create a quote', day_create_quote IS NOT NULL, converted_to_paid FROM trial_view
    UNION ALL SELECT 'Schedule a job', day_schedule_job IS NOT NULL, converted_to_paid FROM trial_view
    UNION ALL SELECT 'Send an invoice', day_send_invoice IS NOT NULL, converted_to_paid FROM trial_view
    UNION ALL SELECT 'Connect payments', day_connect_payments IS NOT NULL, converted_to_paid FROM trial_view
    UNION ALL SELECT 'Invite a team member', day_invite_team IS NOT NULL, converted_to_paid
        FROM trial_view WHERE multi_person
)
SELECT
    action,
    ROUND(AVG(did::INT), 3)                                   AS share_reaching,
    ROUND(AVG(CASE WHEN did THEN converted_to_paid::INT END), 3)     AS conversion_if_done,
    ROUND(AVG(CASE WHEN NOT did THEN converted_to_paid::INT END), 3) AS conversion_if_not,
    ROUND(AVG(CASE WHEN did THEN converted_to_paid::INT END)
          - AVG(CASE WHEN NOT did THEN converted_to_paid::INT END), 3) AS raw_gap
FROM long
GROUP BY action
ORDER BY raw_gap DESC;
