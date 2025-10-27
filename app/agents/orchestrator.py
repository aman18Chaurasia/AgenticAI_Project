import argparse
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlmodel import Session, select
from .news_agent import NewsAgent
from .mapping_agent import MappingAgent
from .planner_agent import PlannerAgent
from .reporter_agent import ReporterAgent
from ..core.db import engine
from ..models.user import User
from ..services.capsules import build_daily_capsule
from ..services.notifier import send_bulk_capsule_emails

logger = logging.getLogger(__name__)


def run_full_agentic_pipeline() -> None:
    """Run complete autonomous pipeline: ingest -> map -> plan -> report -> email"""
    logger.info("Starting Autonomous UPSC Pipeline - %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # Run all agents
    agents = [NewsAgent(), MappingAgent(), PlannerAgent(), ReporterAgent()]
    for agent in agents:
        result = agent.run()
        status = "OK" if result.success else "FAIL"
        logger.info("[%s] %s: %s", status, result.name, result.detail)

    # Generate and send daily capsules
    with Session(engine) as session:
        # Build today's capsule
        capsule = build_daily_capsule(session)

        # Get all subscribed users
        subscribers = session.exec(
            select(User.email).where(
                User.daily_capsule_subscribed == True,
                User.is_active == True
            )
        ).all()

        if subscribers and capsule["items"]:
            # Send emails to all subscribers
            results = send_bulk_capsule_emails(list(subscribers), capsule)
            logger.info("Emails sent: %s, failed: %s", results['sent'], results['failed'])
            logger.info("Capsule items: %s", len(capsule['items']))
        else:
            logger.info("No subscribers or no content to send")

    logger.info("Autonomous pipeline completed.")


def run_once() -> None:
    """Run pipeline once for testing"""
    run_full_agentic_pipeline()


def schedule_daily() -> None:
    """Schedule autonomous pipeline to run daily at 6 AM"""
    logger.info("Starting Autonomous UPSC Pipeline Scheduler...")
    logger.info("Daily execution: 6:00 AM")
    logger.info("Press Ctrl+C to stop")

    sched = BlockingScheduler()
    sched.add_job(
        run_full_agentic_pipeline,
        "cron",
        hour=6,
        minute=0,
        id="daily_upsc_pipeline"
    )

    try:
        sched.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sched.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--schedule", action="store_true")
    args = parser.parse_args()
    if args.run_once:
        run_once()
    elif args.schedule:
        schedule_daily()
    else:
        run_once()
