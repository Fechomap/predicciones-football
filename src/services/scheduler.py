"""Task scheduler for periodic operations"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class BotScheduler:
    """Manages scheduled tasks for the bot"""

    def __init__(self, bot_service):
        """
        Initialize scheduler

        Args:
            bot_service: BotService instance to run tasks
        """
        self.bot_service = bot_service
        self.scheduler = AsyncIOScheduler()

        logger.debug("Scheduler initialized")

    def start(self):
        """Start the scheduler"""
        # Main task: Check fixtures every X minutes
        self.scheduler.add_job(
            func=self.bot_service.check_fixtures,
            trigger=IntervalTrigger(minutes=Config.CHECK_INTERVAL),
            id="check_fixtures",
            name="Check upcoming fixtures",
            replace_existing=True
        )

        # Daily summary at 9:00 AM
        self.scheduler.add_job(
            func=self.bot_service.send_daily_summary,
            trigger=CronTrigger(hour=9, minute=0),
            id="daily_summary",
            name="Send daily summary",
            replace_existing=True
        )

        # Sync leagues daily at midnight
        self.scheduler.add_job(
            func=self.bot_service.sync_leagues,
            trigger=CronTrigger(hour=0, minute=0),
            id="sync_leagues",
            name="Sync leagues",
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Scheduler started")

        # Log scheduled jobs
        for job in self.scheduler.get_jobs():
            logger.info(f"Scheduled job: {job.name} - Next run: {job.next_run_time}")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def run_now(self, job_id: str):
        """
        Run a scheduled job immediately

        Args:
            job_id: Job ID to run
        """
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Job {job_id} scheduled to run immediately")
        else:
            logger.warning(f"Job {job_id} not found")
