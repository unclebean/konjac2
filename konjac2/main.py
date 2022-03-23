import os
import logging
import uvicorn
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from konjac2.bot.telegram_bot import startup_bot


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    file_path = os.environ.get("konjac_log", "./logs/konjac_api.log")
    logger = logging.getLogger()
    fhandler = RotatingFileHandler(file_path, maxBytes=10000000, backupCount=5)
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s")
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)
    logger.setLevel(logging.INFO)
    startup_bot()


@app.get("/")
async def root():
    return "KONJAC BACKEND"


if __name__ == "__main__":
    # os.environ["konjac_log"] = "../logs/konjac_api.log"
    uvicorn.run(app, host="0.0.0.0", port=5555)
