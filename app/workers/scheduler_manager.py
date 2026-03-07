"""Manager for background scheduler tasks."""
import asyncio
from loguru import logger

from app.workers.reply_checker import start_reply_checker
from app.workers.followup_scheduler import start_followup_scheduler
from app.core.config import settings


class SchedulerManager:
    """Manages background scheduler tasks."""
    
    def __init__(self):
        """Initialize scheduler manager."""
        self.tasks = []
    
    async def start_all(self):
        """Start all background schedulers."""
        logger.info("Starting background schedulers...")
        
        try:
            # Start reply checker
            reply_task = asyncio.create_task(
                start_reply_checker(settings.SHEETS_SPREADSHEET_ID)
            )
            self.tasks.append(reply_task)
            logger.info("✓ Reply checker started")
            
            # Start follow-up scheduler
            followup_task = asyncio.create_task(
                start_followup_scheduler(settings.SHEETS_SPREADSHEET_ID)
            )
            self.tasks.append(followup_task)
            logger.info("✓ Follow-up scheduler started")
            
            logger.info("All background schedulers running")
            
            # Wait for all tasks
            await asyncio.gather(*self.tasks)
            
        except Exception as e:
            logger.error(f"Error starting schedulers: {e}")
            raise
    
    async def stop_all(self):
        """Stop all background schedulers."""
        logger.info("Stopping background schedulers...")
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("All schedulers stopped")


# Global scheduler manager instance
scheduler_manager = SchedulerManager()


async def start_schedulers():
    """Start background schedulers."""
    await scheduler_manager.start_all()


async def stop_schedulers():
    """Stop background schedulers."""
    await scheduler_manager.stop_all()
