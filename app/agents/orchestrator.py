import argparse
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from .news_agent import NewsAgent
from .mapping_agent import MappingAgent
from .planner_agent import PlannerAgent
from .reporter_agent import ReporterAgent

logger = logging.getLogger(__name__)


def run_once() -> None:
    agents = [NewsAgent(), MappingAgent(), PlannerAgent(), ReporterAgent()]
    for a in agents:
        res = a.run()
        print(f"{res.name}: {res.success} - {res.detail}")


def schedule_daily() -> None:
    sched = BlockingScheduler()
    sched.add_job(run_once, "cron", hour=6, minute=0)
    sched.start()


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

