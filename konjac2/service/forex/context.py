import v20
from konjac2.config import settings


def get_context():
    return v20.Context(
        settings.oanda_url,
        443,
        True,
        application=settings.app_name,
        token=settings.oanda_token,
        datetime_format="RFC3339",
        poll_timeout=20,
    )


def get_account():
    return settings.oanda_account
