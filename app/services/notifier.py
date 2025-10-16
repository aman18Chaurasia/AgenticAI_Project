import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from ..core.config import get_settings

def send_daily_capsule_email(recipient_email: str, capsule_data: Dict[str, Any]) -> bool:
    """Send daily capsule via email"""
    settings = get_settings()
    
    if not all([settings.smtp_server, settings.smtp_port, settings.smtp_username, settings.smtp_password]):
        print("SMTP not configured, skipping email")
        return False
    
    try:
        # Create email content
        html_content = generate_capsule_html(capsule_data)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Daily UPSC Capsule - {capsule_data['date']}"
        msg['From'] = settings.smtp_username
        msg['To'] = recipient_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        return False

def generate_capsule_html(capsule_data: Dict[str, Any]) -> str:
    """Generate HTML content for daily capsule"""
    items_html = ""
    
    for item in capsule_data.get('items', []):
        topics_html = ""
        if item.get('topics'):
            topics_html = "<ul>"
            for topic in item['topics']:
                topics_html += f"<li><strong>{topic['paper']}</strong>: {topic['topic']} (Score: {topic['score']:.2f})</li>"
            topics_html += "</ul>"
        
        pyqs_html = ""
        if item.get('pyqs'):
            pyqs_html = "<p><strong>Related PYQs:</strong></p><ul>"
            for pyq in item['pyqs'][:3]:  # Show top 3 PYQs
                pyqs_html += f"<li>{pyq['question']} ({pyq['year']})</li>"
            pyqs_html += "</ul>"
        
        items_html += f"""
        <div style="border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px;">
            <h3><a href="{item['url']}" style="color: #2c5aa0; text-decoration: none;">{item['title']}</a></h3>
            <p>{item.get('summary', 'No summary available')}</p>
            {f"<p><strong>Syllabus Mapping:</strong></p>{topics_html}" if topics_html else ""}
            {pyqs_html}
            <p><small><strong>Source:</strong> <a href="{item['url']}">{item['url']}</a></small></p>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Daily UPSC Capsule</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2c5aa0; text-align: center;">CivicBriefs.ai - Daily UPSC Capsule</h1>
        <h2 style="color: #666; text-align: center;">{capsule_data['date']}</h2>
        
        <p>Dear UPSC Aspirant,</p>
        <p>Here's your daily dose of UPSC-relevant news with syllabus mapping and related Previous Year Questions (PYQs):</p>
        
        {items_html}
        
        <hr style="margin: 30px 0;">
        <p style="text-align: center; color: #666; font-size: 12px;">
            This is an automated email from CivicBriefs.ai<br>
            Stay updated, stay prepared!
        </p>
    </body>
    </html>
    """

def send_bulk_capsule_emails(subscribers: List[str], capsule_data: Dict[str, Any]) -> Dict[str, int]:
    """Send capsule to multiple subscribers"""
    results = {"sent": 0, "failed": 0}
    
    for email in subscribers:
        if send_daily_capsule_email(email, capsule_data):
            results["sent"] += 1
        else:
            results["failed"] += 1
    
    return results

def send_password_reset_email(recipient_email: str, reset_link: str) -> bool:
    """Send password reset email"""
    settings = get_settings()
    
    if not all([settings.smtp_server, settings.smtp_port, settings.smtp_username, settings.smtp_password]):
        print("SMTP not configured, skipping email")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Password Reset - CivicBriefs.ai"
        msg['From'] = settings.smtp_username
        msg['To'] = recipient_email
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your CivicBriefs.ai account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_link}" style="background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Failed to send reset email to {recipient_email}: {e}")
        return False