import os
import logging
import uvicorn
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from konjac2.bot.telegram_bot import startup_bot
from konjac2.routers.daily_trend import router as TrendRouter
from konjac2.routers.chart import router as ChartRouter
from konjac2.jobs.scanner import scanner_job
from konjac2.config import settings

app = FastAPI()
app.include_router(TrendRouter)
app.include_router(ChartRouter)


@app.on_event("startup")
async def startup_event():
    file_path = os.environ.get("konjac_log", "./logs/konjac_api.log")
    logger = logging.getLogger()
    fhandler = RotatingFileHandler(file_path, maxBytes=10000000, backupCount=5)
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s")
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)
    logger.setLevel(logging.INFO)


@app.on_event("startup")
async def start_bot():
    startup_bot()


@app.on_event("startup")
async def start_job():
    if settings.run_cron_job:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(scanner_job, CronTrigger.from_crontab("*/30 * * * *"))
        # scheduler.add_job(short_smart_bot, CronTrigger.from_crontab("*/5 * * * *"))
        scheduler.start()
        print("***** loaded cron jobs *****")


@app.get("/")
async def root():
    return "KONJAC BACKEND"


if __name__ == "__main__":
    # os.environ["konjac_log"] = "../logs/konjac_api.log"
    uvicorn.run(app, host="0.0.0.0", port=5555)
