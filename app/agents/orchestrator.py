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
    print(f"\nStarting Autonomous UPSC Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Run all agents
    agents = [NewsAgent(), MappingAgent(), PlannerAgent(), ReporterAgent()]
    for agent in agents:
        result = agent.run()
        status = "OK" if result.success else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

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
            print(f"Emails sent: {results['sent']}, failed: {results['failed']}")
            print(f"Capsule items: {len(capsule['items'])}")
        else:
            print("No subscribers or no content to send")

    print("\nAutonomous pipeline completed.")
    print("=" * 60)


def run_once() -> None:
    """Run pipeline once for testing"""
    run_full_agentic_pipeline()


def schedule_daily() -> None:
    """Schedule autonomous pipeline to run daily at 6 AM"""
    print("Starting Autonomous UPSC Pipeline Scheduler...")
    print("Daily execution: 6:00 AM")
    print("Press Ctrl+C to stop\n")

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
        print("\nScheduler stopped by user")
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
