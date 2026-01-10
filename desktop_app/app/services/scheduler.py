"""
Background Scheduler Service

Handles automated background tasks like workflow execution and data syncing.
"""

from apscheduler.schedulers.background import BackgroundScheduler as APScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Background task scheduler for automated workflows"""

    def __init__(self, db_manager, config_manager):
        """
        Initialize background scheduler

        Args:
            db_manager: Database manager instance
            config_manager: Configuration manager instance
        """
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.scheduler = APScheduler()
        self.is_running = False

    def start(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        try:
            # Get workflow settings from config
            workflows_enabled = self.config_manager.get("workflows.enabled", True)
            interval_minutes = self.config_manager.get("workflows.auto_run_interval_minutes", 30)

            if workflows_enabled:
                # Schedule workflow execution
                self.scheduler.add_job(
                    self._run_workflows,
                    trigger=IntervalTrigger(minutes=interval_minutes),
                    id='workflow_execution',
                    name='Execute collection workflows',
                    replace_existing=True
                )

                logger.info(f"Scheduled workflows to run every {interval_minutes} minutes")

            # Schedule data sync (if enabled)
            xero_auto_sync = self.config_manager.get("integrations.xero.auto_sync", False)
            if xero_auto_sync:
                sync_interval_hours = self.config_manager.get("integrations.xero.sync_interval_hours", 24)
                self.scheduler.add_job(
                    self._sync_xero,
                    trigger=IntervalTrigger(hours=sync_interval_hours),
                    id='xero_sync',
                    name='Sync with Xero',
                    replace_existing=True
                )

                logger.info(f"Scheduled Xero sync every {sync_interval_hours} hours")

            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            logger.info("Background scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

    def stop(self):
        """Stop the background scheduler"""
        if not self.is_running:
            return

        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Background scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    def _run_workflows(self):
        """Execute automated workflows (called by scheduler)"""
        try:
            logger.info("Running automated workflows...")

            # TODO: Import and call workflow engine
            # from ..services.workflow_engine import workflow_engine
            # session = self.db_manager.get_session()
            # result = await workflow_engine.process_all_invoices(session)
            # session.close()
            # logger.info(f"Workflows completed: {result}")

            logger.info("Workflow execution placeholder (not yet implemented)")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

    def _sync_xero(self):
        """Sync data with Xero (called by scheduler)"""
        try:
            logger.info("Syncing with Xero...")

            # TODO: Import and call Xero client
            # from ..services.xero_client import xero_client
            # if xero_client.is_connected:
            #     invoices = xero_client.sync_invoices()
            #     logger.info(f"Synced {len(invoices)} invoices from Xero")

            logger.info("Xero sync placeholder (not yet implemented)")

        except Exception as e:
            logger.error(f"Xero sync failed: {e}")

    def trigger_workflow_now(self):
        """Manually trigger workflow execution"""
        logger.info("Manual workflow trigger requested")
        self._run_workflows()

    def trigger_sync_now(self):
        """Manually trigger Xero sync"""
        logger.info("Manual Xero sync trigger requested")
        self._sync_xero()

    def get_next_run_time(self, job_id: str):
        """Get next scheduled run time for a job"""
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None

    def pause(self):
        """Pause all scheduled jobs"""
        if self.is_running:
            self.scheduler.pause()
            logger.info("Scheduler paused")

    def resume(self):
        """Resume all scheduled jobs"""
        if self.is_running:
            self.scheduler.resume()
            logger.info("Scheduler resumed")
