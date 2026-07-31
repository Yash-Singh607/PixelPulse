"""
Backward-compatible wrapper entrypoint for synthetic data generation.
Delegates execution to the modular core generator in src.data_generator.
"""

from src.data_generator import generate_pixel_loft_data
from config import DB_PATH

if __name__ == "__main__":
    print("Executing synthetic dataset generator wrapper...")
    users, events, subs = generate_pixel_loft_data(n_users=6000, random_seed=42, db_path=DB_PATH)
    print(f"Users: {len(users)}")
    print(f"Events: {len(events)}")
    print(f"Subscriptions: {len(subs)}")
    print(events["event_name"].value_counts().to_string())
