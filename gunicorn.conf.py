import os

workers = 3
bind = "0.0.0.0:8000"
timeout = 120
preload_app = True


def post_fork(server, worker):
    """Réinitialise Sentry dans chaque worker après le fork."""
    dsn = os.environ.get("SENTRY_DSN", "")
    if dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            send_default_pii=False,
            traces_sample_rate=0.1,
        )
