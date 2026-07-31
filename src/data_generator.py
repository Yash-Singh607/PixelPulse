"""
Synthetic Data Generation Engine for PixelLoft Freemium Photo-Editing Application.
Simulates realistic product analytics event streams, users, onboarding A/B test, and subscriptions.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Union
import numpy as np
import pandas as pd

from config import DB_PATH
from src.database import DatabaseEngine

logger = logging.getLogger(__name__)


def generate_pixel_loft_data(
    n_users: int = 6000,
    random_seed: int = 42,
    db_path: Union[str, Path] = DB_PATH,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generates synthetic realistic data for PixelLoft users, events, and subscriptions.
    Saves tables directly into the SQLite database specified by db_path.
    """
    rng = np.random.default_rng(random_seed)

    start_date = datetime.strptime("2025-01-01", "%Y-%m-%d")
    end_date = datetime.strptime("2025-12-31", "%Y-%m-%d")
    total_days = (end_date - start_date).days

    channels = ["organic_search", "paid_social", "referral", "influencer", "app_store_featured"]
    channel_weights = [0.30, 0.28, 0.15, 0.17, 0.10]
    channel_quality = {
        "organic_search": 1.15,
        "paid_social": 0.80,
        "referral": 1.30,
        "influencer": 0.75,
        "app_store_featured": 1.05,
    }

    platforms = ["iOS", "Android"]
    countries = ["US", "IN", "UK", "BR", "DE", "CA"]
    country_weights = [0.35, 0.25, 0.12, 0.10, 0.10, 0.08]

    # 1. USERS
    signup_offsets = np.sort(
        rng.choice(
            np.arange(total_days),
            size=n_users,
            p=(np.arange(total_days) + 50) / (np.arange(total_days) + 50).sum(),
        )
    )

    users = pd.DataFrame(
        {
            "user_id": np.arange(1, n_users + 1),
            "signup_date": [start_date + timedelta(days=int(d)) for d in signup_offsets],
            "channel": rng.choice(channels, n_users, p=channel_weights),
            "platform": rng.choice(platforms, n_users, p=[0.55, 0.45]),
            "country": rng.choice(countries, n_users, p=country_weights),
        }
    )

    # 2. ONBOARDING EXPERIMENT ASSIGNMENT
    users["experiment_group"] = rng.choice(
        ["control_self_serve", "treatment_guided_edit"], n_users, p=[0.5, 0.5]
    )

    # 3. FUNNEL EVENTS
    events = []

    def maybe_fire(user_id, event_name, event_date, prob):
        if rng.random() < prob:
            events.append((user_id, event_name, event_date))
            return True
        return False

    for _, u in users.iterrows():
        uid = u["user_id"]
        base_q = channel_quality[u["channel"]]
        exp_lift = 0.045 if u["experiment_group"] == "treatment_guided_edit" else 0.0

        signup_dt = u["signup_date"]
        events.append((uid, "signup", signup_dt))

        p_onboard = min(0.95, 0.55 * base_q + exp_lift)
        onboarded = maybe_fire(
            uid,
            "onboarding_complete",
            signup_dt + timedelta(hours=int(rng.integers(1, 48))),
            p_onboard,
        )

        if onboarded:
            p_edit = min(0.95, 0.70 * base_q + exp_lift * 0.6)
            edited = maybe_fire(
                uid, "first_edit", signup_dt + timedelta(days=int(rng.integers(0, 3))), p_edit
            )
        else:
            edited = False

        if edited:
            p_trial = min(0.9, 0.35 * base_q)
            trial = maybe_fire(
                uid,
                "trial_started",
                signup_dt + timedelta(days=int(rng.integers(1, 7))),
                p_trial,
            )
        else:
            trial = False

        if trial:
            p_sub = min(0.85, 0.40 * base_q)
            subscribed = maybe_fire(
                uid,
                "subscribed",
                signup_dt + timedelta(days=int(rng.integers(7, 14))),
                p_sub,
            )
        else:
            subscribed = False

        # Retention logins
        if onboarded:
            active = True
            day_offset = 0
            retention_strength = base_q * (1.6 if subscribed else 1.0)
            while active and day_offset < 200:
                gap = int(rng.geometric(p=max(0.03, 0.12 / retention_strength)))
                day_offset += gap
                login_date = signup_dt + timedelta(days=day_offset)
                if login_date > end_date:
                    break
                events.append((uid, "app_open", login_date))
                if rng.random() < 0.06 / retention_strength:
                    active = False

    events_df = pd.DataFrame(events, columns=["user_id", "event_name", "event_date"])
    events_df = events_df.sort_values(["user_id", "event_date"]).reset_index(drop=True)

    # 4. SUBSCRIPTIONS
    sub_events = events_df[events_df["event_name"] == "subscribed"].copy()
    plans = ["monthly", "annual"]
    plan_price = {"monthly": 9.99, "annual": 79.99}

    subs = []
    for _, row in sub_events.iterrows():
        plan = rng.choice(plans, p=[0.65, 0.35])
        subs.append((row["user_id"], row["event_date"], plan, plan_price[plan]))

    subscriptions = pd.DataFrame(
        subs, columns=["user_id", "subscribed_date", "plan", "price_usd"]
    )

    # Save to SQLite Database using DatabaseEngine
    db = DatabaseEngine(db_path=db_path)
    with db.get_connection() as conn:
        users.to_sql("users", conn, if_exists="replace", index=False)
        events_df.to_sql("events", conn, if_exists="replace", index=False)
        subscriptions.to_sql("subscriptions", conn, if_exists="replace", index=False)

    db.create_indexes()

    logger.info(
        f"Data generated successfully: {len(users)} users, {len(events_df)} events, {len(subscriptions)} subscriptions."
    )
    return users, events_df, subscriptions
