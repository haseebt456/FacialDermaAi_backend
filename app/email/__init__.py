import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, html_body: str):
    """
    Send an email asynchronously using Gmail SMTP
    Failures are logged but do not raise exceptions
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = settings.EMAIL_USER
        message["To"] = to_email
        message["Subject"] = subject
        
        # Attach HTML body
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.EMAIL_USER,
            password=settings.EMAIL_PASS,
        )
        
        logger.info(f"Email sent successfully to {to_email}")
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        # Do not raise - email failures should not break the API


async def send_welcome_email(email: str, username: str):
    """Send welcome email on user signup"""
    subject = "Welcome to FacialDerma AI!"
    html_body = f"""
    <html>
        <body>
            <h2>Welcome to FacialDerma AI, {username}!</h2>
            <p>Thank you for registering with us. We're excited to have you on board.</p>
            <p>You can now log in and start using our facial dermatology AI services.</p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(email, subject, html_body)


async def send_login_notification_email(email: str, username: str, ip_address: str):
    """Send login notification email with IP address"""
    subject = "New Login to Your FacialDerma AI Account"
    html_body = f"""
    <html>
        <body>
            <h2>New Login Detected</h2>
            <p>Hello {username},</p>
            <p>We detected a new login to your FacialDerma AI account.</p>
            <p><strong>IP Address:</strong> {ip_address}</p>
            <p><strong>Time:</strong> Just now</p>
            <br>
            <p>If this wasn't you, please secure your account immediately.</p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(email, subject, html_body)
