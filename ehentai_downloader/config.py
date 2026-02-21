from fake_useragent import UserAgent

DEFAULT_DOWNLOAD_FOLDER = "Downloads"
KB = 1024
CHUNK_SIZE = 16 * KB
HTTP_RATE_LIMIT = 429
CONNECTION_TIMEOUT = 30.0
RATE_LIMIT_SLEEP = 60

USER_AGENT_ROTATOR = UserAgent()


def random_user_agent() -> str:
    return str(USER_AGENT_ROTATOR.firefox)
