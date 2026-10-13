"""Sends the weekly link email over SMTP."""

import html
import smtplib
from email.message import EmailMessage

from .config import settings


def week_url(token: str) -> str:
    return f"{settings.base_url}/w/{token}"


def send_week_email(week: dict) -> None:
    if not (settings.smtp_user and settings.smtp_password and settings.email_to):
        raise RuntimeError("Email is not configured: set SMTP_USER, SMTP_PASSWORD and EMAIL_TO in .env")

    url = week_url(week["token"])
    titles = [r["title"] for r in week["recipes"]]

    msg = EmailMessage()
    msg["Subject"] = f"This week's dinner ideas ({week['week_of']})"
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(settings.email_to)
    msg.set_content(
        f"{len(titles)} new recipes are ready for this week:\n\n"
        + "\n".join(f"- {t}" for t in titles)
        + f"\n\nPick your meals and export the shopping list here:\n{url}\n"
    )
    items = "".join(f"<li>{html.escape(t)}</li>" for t in titles)
    msg.add_alternative(
        f"""<div style="font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:16px;color:#222">
<p>{len(titles)} new recipes are ready for this week:</p>
<ul>{items}</ul>
<p><a href="{html.escape(url)}" style="display:inline-block;background:#2f6b4f;color:#fff;
padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:600">Open this week's recipes</a></p>
</div>""",
        subtype="html",
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
