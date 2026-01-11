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

            from ..services.workflow_engine import get_workflow_engine

            engine = get_workflow_engine(self.db_manager)
            session = self.db_manager.get_session()

            result = engine.run_workflows(session)
            session.close()

            logger.info(f"Workflows completed: {result}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

    def _sync_xero(self):
        """Sync data with Xero (called by scheduler)"""
        try:
            logger.info("Syncing with Xero...")

            from ..services.xero_client import xero_client

            if xero_client.is_connected():
                # Sync invoices from Xero
                invoices_data = xero_client.get_aged_receivables()

                if invoices_data:
                    # Import to database
                    from ..models.database import Customer, Invoice, InvoiceStatus, AgingBucket
                    from datetime import date

                    session = self.db_manager.get_session()
                    sync_count = 0

                    try:
                        for data in invoices_data:
                            # Find or create customer
                            customer = session.query(Customer).filter_by(
                                customer_id=data.get('customer_id')
                            ).first()

                            if not customer:
                                customer = Customer(
                                    customer_id=data.get('customer_id', f"XERO-{sync_count}"),
                                    company_name=data['customer_name'],
                                    email=data.get('email'),
                                    current_balance=data['amount_outstanding']
                                )
                                session.add(customer)
                                session.flush()

                            # Find or update invoice
                            invoice = session.query(Invoice).filter_by(
                                invoice_number=data['invoice_number']
                            ).first()

                            if not invoice:
                                invoice = Invoice(
                                    invoice_number=data['invoice_number'],
                                    customer_id=customer.id,
                                    invoice_date=data.get('invoice_date', date.today()),
                                    due_date=data.get('due_date', date.today()),
                                    original_amount=data.get('original_amount', data['amount_outstanding']),
                                    amount_outstanding=data['amount_outstanding'],
                                    amount_paid=data.get('amount_paid', 0.0),
                                    status=InvoiceStatus.OPEN if data['amount_outstanding'] > 0 else InvoiceStatus.PAID,
                                    aging_bucket=data.get('aging_bucket', AgingBucket.CURRENT),
                                    days_outstanding=data.get('days_overdue', 0)
                                )
                                session.add(invoice)
                            else:
                                # Update existing
                                invoice.amount_outstanding = data['amount_outstanding']
                                invoice.amount_paid = data.get('amount_paid', invoice.amount_paid)
                                invoice.status = InvoiceStatus.OPEN if data['amount_outstanding'] > 0 else InvoiceStatus.PAID

                            sync_count += 1

                        session.commit()
                        logger.info(f"Synced {sync_count} invoices from Xero")

                    except Exception as e:
                        session.rollback()
                        raise
                    finally:
                        session.close()
            else:
                logger.info("Xero not connected - skipping sync")

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
