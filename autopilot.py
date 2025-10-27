#!/usr/bin/env python3
"""
Autonomous entrypoint: boot backend, scheduler, agents, and reports.

Usage:
  python autopilot.py --all
  python autopilot.py --server
  python autopilot.py --scheduler
  python autopilot.py --run-once
  python autopilot.py --init-db
"""
from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Ensure app package is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.core.db import engine
from sqlmodel import SQLModel, Session, select


logger = logging.getLogger("autopilot")


def _configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _init_db() -> None:
    from app.services.bootstrap import seed_basics
    # Import models to register with SQLModel
    from app.models import user as _mu  # noqa: F401
    from app.models import content as _mc  # noqa: F401
    from app.models import tests as _mt  # noqa: F401
    SQLModel.metadata.create_all(engine)
    seed_basics()
    logger.info("Database initialized and seeded")


def _start_server() -> subprocess.Popen:
    settings = get_settings()
    logger.info("Starting API server at http://%s:%s", settings.app_host, settings.app_port)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            settings.app_host,
            "--port",
            str(settings.app_port),
        ]
        + (["--reload"] if os.getenv("UVICORN_RELOAD", "0") == "1" else []),
        stdout=None,
        stderr=None,
    )
    return proc


def _schedule_jobs(sched: BackgroundScheduler) -> None:
    from app.agents.orchestrator import run_full_agentic_pipeline
    from app.services.tests import generate_daily_quiz
    from app.services.reports import build_weekly_report
    from app.services.notifier import send_bulk_html_emails
    from app.models.user import User

    settings = get_settings()

    def job_pipeline():
        run_full_agentic_pipeline()

    def job_quiz():
        # ensure a quiz exists for today
        with Session(engine) as session:
            payload = generate_daily_quiz(session)
            logger.info("Daily quiz prepared: %s with %d questions", payload.get("name"), len(payload.get("questions", [])))

    def job_weekly_report():
        with Session(engine) as session:
            report = build_weekly_report(session)
            subs = session.exec(
                select(User.email).where(User.weekly_report_subscribed == True, User.is_active == True)  # type: ignore
            ).all()
            recipients = [e for (e,) in subs] if subs and isinstance(subs[0], tuple) else list(subs)
            items = "".join(
                [
                    f"<li><a href='{h.get('url')}'>{h.get('title')}</a> <small>({h.get('date')})</small></li>"
                    for h in report.get("highlights", [])
                ]
            )
            html = (
                f"<h2>Weekly UPSC Highlights ({report['week_start']} to {report['week_end']})</h2>"
                f"<p><strong>Tests recorded:</strong> {report['progress']['tests_recorded']} | "
                f"<strong>Average score:</strong> {report['progress']['average_score']}</p>"
                f"<ol>{items}</ol>"
                f"<p>— CivicBriefs.ai</p>"
            )
            res = send_bulk_html_emails(recipients, f"Weekly UPSC Report ({report['week_end']})", html)
            logger.info("Weekly report sent: %s", res)

    # Pipeline daily
    sched.add_job(job_pipeline, CronTrigger.from_crontab(settings.schedule_cron_daily), id="daily_pipeline", replace_existing=True)
    # Daily quiz
    sched.add_job(job_quiz, CronTrigger.from_crontab(settings.schedule_cron_quiz), id="daily_quiz", replace_existing=True)
    # Weekly report
    sched.add_job(job_weekly_report, CronTrigger.from_crontab(settings.schedule_cron_weekly_report), id="weekly_report", replace_existing=True)


def main(argv: Optional[list[str]] = None) -> int:
    _configure_logging()
    parser = argparse.ArgumentParser(description="Daily UPSC Capsule AI Platform - Autopilot")
    parser.add_argument("--all", action="store_true", help="Initialize DB, start server and scheduler")
    parser.add_argument("--init-db", action="store_true", help="Initialize database and seed data")
    parser.add_argument("--server", action="store_true", help="Start API server only")
    parser.add_argument("--scheduler", action="store_true", help="Start background scheduler only")
    parser.add_argument("--run-once", action="store_true", help="Run agentic pipeline once and exit")
    args = parser.parse_args(argv)

    if args.run_once:
        from app.agents.orchestrator import run_full_agentic_pipeline

        _init_db()
        run_full_agentic_pipeline()
        return 0

    server_proc: Optional[subprocess.Popen] = None
    sched: Optional[BackgroundScheduler] = None

    if args.init_db or args.all:
        _init_db()

    try:
        if args.server or args.all:
            server_proc = _start_server()
            # small grace to allow server to bind
            time.sleep(1.0)

        if args.scheduler or args.all:
            sched = BackgroundScheduler()
            _schedule_jobs(sched)
            sched.start()
            logger.info("Scheduler started with jobs: %s", [j.id for j in sched.get_jobs()])

        if not any([args.server, args.scheduler, args.all]):
            parser.print_help()
            return 1

        # Wait until interrupted
        def _handle(sig, frame):  # type: ignore[no-redef]
            logger.info("Signal received: %s. Shutting down...", sig)
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)

        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("Stopping services...")
        return 0
    finally:
        if sched:
            sched.shutdown(wait=False)
        if server_proc and server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except Exception:
                server_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
