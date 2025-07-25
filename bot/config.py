import os
from dotenv import load_dotenv

_ = load_dotenv()


def get_token():
    token = os.getenv("token")
    if not token:
        raise ValueError("Bot token not found. Add it to your .env file.")
    return token


def get_owner_id():
    uid = os.getenv("userid")
    if not uid:
        raise ValueError("Please set your userid in .env")
    return int(uid)


def get_poll_interval():
    interval = os.getenv("POLL_INTERVAL_MINUTES")
    if not interval:
        return 15
    return int(interval)
