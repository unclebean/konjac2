from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str
    run_cron_job: bool
    oanda_url: str
    oanda_token: str
    oanda_account: str
    units: int
    ftx_spot_api_key: str
    ftx_spot_secret: str
    ftx_future_api_key: str
    ftx_future_secret: str
    binance_api_key: str
    binance_secret: str

    class Config:
        env_file = ".env"


settings = Settings()
