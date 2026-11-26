-- One row per trial: the first day (0 = sign-up day) each setup action happened, yes or no flags,
-- and whether the trial converted to paid.
CREATE OR REPLACE VIEW first_action_day AS
SELECT e.trial_id, e.action, MIN(DATE_DIFF('day', t.signup_date, e.event_date)) AS first_day
FROM trial_events e JOIN trials t USING (trial_id)
GROUP BY 1, 2;

CREATE OR REPLACE VIEW trial_view AS
SELECT
    t.trial_id, t.trade, t.team_size, t.signup_source, t.signup_device,
    t.team_size <> 'Solo' AS multi_person,
    MAX(CASE WHEN f.action = 'add_client' THEN f.first_day END)       AS day_add_client,
    MAX(CASE WHEN f.action = 'create_quote' THEN f.first_day END)     AS day_create_quote,
    MAX(CASE WHEN f.action = 'schedule_job' THEN f.first_day END)     AS day_schedule_job,
    MAX(CASE WHEN f.action = 'send_invoice' THEN f.first_day END)     AS day_send_invoice,
    MAX(CASE WHEN f.action = 'connect_payments' THEN f.first_day END) AS day_connect_payments,
    MAX(CASE WHEN f.action = 'invite_team' THEN f.first_day END)      AS day_invite_team,
    o.converted_to_paid
FROM trials t
JOIN trial_outcomes o USING (trial_id)
LEFT JOIN first_action_day f USING (trial_id)
GROUP BY ALL;
