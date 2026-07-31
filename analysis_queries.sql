-- ============================================================================
-- PixelLoft Product Analytics — SQL Analysis
-- Author: Yash Pratap Singh
--
-- Dataset: 6,000 users of a freemium photo-editing app over 2025.
-- Tables:
--   users          (user_id, signup_date, channel, platform, country, experiment_group)
--   events         (user_id, event_name, event_date)  -- signup, onboarding_complete,
--                                                         first_edit, trial_started,
--                                                         subscribed, app_open
--   subscriptions  (user_id, subscribed_date, plan, price_usd)
--
-- Four analyses, each answering a real product question:
--   1. Signup -> Paid funnel, broken down by acquisition channel
--   2. Monthly cohort retention (are we retaining users better over time?)
--   3. A/B test readout: does the new "guided edit" onboarding lift activation?
--   4. Revenue segmentation: which channels/plans actually drive revenue?
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. FUNNEL ANALYSIS BY CHANNEL
-- Question: Where in the funnel are we losing the most users, and does that
-- differ by acquisition channel? (Guides where to invest fix-it effort.)
-- ----------------------------------------------------------------------------
WITH funnel AS (
    SELECT
        u.channel,
        COUNT(DISTINCT u.user_id) AS signups,
        COUNT(DISTINCT CASE WHEN e.event_name = 'onboarding_complete' THEN e.user_id END) AS onboarded,
        COUNT(DISTINCT CASE WHEN e.event_name = 'first_edit' THEN e.user_id END) AS edited,
        COUNT(DISTINCT CASE WHEN e.event_name = 'trial_started' THEN e.user_id END) AS trialed,
        COUNT(DISTINCT CASE WHEN e.event_name = 'subscribed' THEN e.user_id END) AS subscribed
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    GROUP BY u.channel
)
SELECT
    channel,
    signups,
    onboarded,
    ROUND(100.0 * onboarded / signups, 1)   AS pct_onboarded,
    edited,
    ROUND(100.0 * edited / NULLIF(onboarded, 0), 1) AS pct_onboarded_to_edit,
    trialed,
    ROUND(100.0 * trialed / NULLIF(edited, 0), 1)   AS pct_edit_to_trial,
    subscribed,
    ROUND(100.0 * subscribed / NULLIF(trialed, 0), 1) AS pct_trial_to_paid,
    ROUND(100.0 * subscribed / signups, 2) AS overall_conversion_pct
FROM funnel
ORDER BY overall_conversion_pct DESC;


-- ----------------------------------------------------------------------------
-- 2. MONTHLY COHORT RETENTION
-- Question: Of users who signed up in month X, what % were still active
-- (had an app_open event) in month 0, 1, 2, 3 after signup?
-- This is the standard cohort-retention table product teams live by.
-- ----------------------------------------------------------------------------
WITH cohort AS (
    SELECT
        user_id,
        strftime('%Y-%m', signup_date) AS cohort_month,
        signup_date
    FROM users
),
activity AS (
    SELECT
        e.user_id,
        c.cohort_month,
        c.signup_date,
        e.event_date,
        CAST(
            (julianday(strftime('%Y-%m-01', e.event_date)) - julianday(strftime('%Y-%m-01', c.signup_date)))
            / 30.4
            AS INTEGER
        ) AS month_number
    FROM events e
    JOIN cohort c ON e.user_id = c.user_id
    WHERE e.event_name = 'app_open'
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT user_id) AS cohort_users
    FROM cohort
    GROUP BY cohort_month
),
retained AS (
    SELECT cohort_month, month_number, COUNT(DISTINCT user_id) AS retained_users
    FROM activity
    WHERE month_number BETWEEN 0 AND 3
    GROUP BY cohort_month, month_number
)
SELECT
    r.cohort_month,
    cs.cohort_users,
    r.month_number,
    r.retained_users,
    ROUND(100.0 * r.retained_users / cs.cohort_users, 1) AS retention_pct
FROM retained r
JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
ORDER BY r.cohort_month, r.month_number;


-- ----------------------------------------------------------------------------
-- 3. A/B TEST READOUT: "guided_edit" vs "self_serve" onboarding
-- Question: Did the new guided onboarding actually lift activation
-- (onboarding_complete rate)? Report group sizes, rates, and absolute lift.
-- (Statistical significance is computed in Python via a z-test on this
-- query's output — see run_analysis.py.)
-- ----------------------------------------------------------------------------
SELECT
    u.experiment_group,
    COUNT(DISTINCT u.user_id) AS users_in_group,
    COUNT(DISTINCT CASE WHEN e.event_name = 'onboarding_complete' THEN e.user_id END) AS activated_users,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN e.event_name = 'onboarding_complete' THEN e.user_id END)
        / COUNT(DISTINCT u.user_id), 2
    ) AS activation_rate_pct
FROM users u
LEFT JOIN events e ON u.user_id = e.user_id
GROUP BY u.experiment_group;


-- ----------------------------------------------------------------------------
-- 4. REVENUE SEGMENTATION
-- Question: Which acquisition channels deliver the best ROI-relevant signal —
-- not just most subscribers, but most revenue and best revenue-per-signup?
-- (The latter matters more: a channel with fewer, higher-value subscribers
-- can beat a channel with many low-value ones.)
-- ----------------------------------------------------------------------------
SELECT
    u.channel,
    COUNT(DISTINCT u.user_id) AS total_signups,
    COUNT(DISTINCT s.user_id) AS paying_users,
    ROUND(SUM(s.price_usd), 2) AS total_revenue_usd,
    ROUND(SUM(s.price_usd) / COUNT(DISTINCT u.user_id), 3) AS revenue_per_signup_usd,
    ROUND(SUM(CASE WHEN s.plan = 'annual' THEN s.price_usd ELSE 0 END)
          / NULLIF(SUM(s.price_usd), 0) * 100, 1) AS pct_revenue_from_annual
FROM users u
LEFT JOIN subscriptions s ON u.user_id = s.user_id
GROUP BY u.channel
ORDER BY revenue_per_signup_usd DESC;
