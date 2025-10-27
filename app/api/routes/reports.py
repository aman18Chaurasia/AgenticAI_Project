from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ...core.db import get_session
from ...models.user import User
from ...services.reports import build_weekly_report
from ...services.notifier import send_bulk_html_emails
from ...core.deps import require_admin

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly")
def weekly_preview(session: Session = Depends(get_session)):
    return build_weekly_report(session)


@router.post("/weekly/send")
def send_weekly(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    report = build_weekly_report(session)
    subs = session.exec(select(User.email).where(User.weekly_report_subscribed == True, User.is_active == True)).all()
    recipients = [e for (e,) in subs] if subs and isinstance(subs[0], tuple) else list(subs)
    # Build simple HTML
    items = "".join([
        f"<li><a href='{h.get('url')}'>{h.get('title')}</a> <small>({h.get('date')})</small></li>" for h in report.get("highlights", [])
    ])
    html = f"""
    <h2>Weekly UPSC Highlights ({report['week_start']} to {report['week_end']})</h2>
    <p><strong>Tests recorded:</strong> {report['progress']['tests_recorded']} | <strong>Average score:</strong> {report['progress']['average_score']}</p>
    <ol>{items}</ol>
    <p>— CivicBriefs.ai</p>
    """
    # Rebuild HTML to avoid encoding artifacts and ensure clean footer
    html = (
        f"<h2>Weekly UPSC Highlights ({report['week_start']} to {report['week_end']})</h2>"
        f"<p><strong>Tests recorded:</strong> {report['progress']['tests_recorded']} | "
        f"<strong>Average score:</strong> {report['progress']['average_score']}</p>"
        f"<ol>{items}</ol>"
        f"<p>— CivicBriefs.ai</p>"
    )
    res = send_bulk_html_emails(recipients, f"Weekly UPSC Report ({report['week_end']})", html)
    return {"recipients": len(recipients), **res}
