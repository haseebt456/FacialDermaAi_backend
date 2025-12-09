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


def parse_user_agent(user_agent: str) -> str:
    """Parse User-Agent string to extract browser and device information"""
    if not user_agent:
        return "Unknown"
    
    ua = user_agent.lower()
    
    # Browser detection
    browsers = {
        'chrome': 'Chrome',
        'firefox': 'Firefox',
        'safari': 'Safari',
        'edge': 'Edge',
        'opera': 'Opera',
        'brave': 'Brave'
    }
    
    browser = "Unknown Browser"
    for key, name in browsers.items():
        if key in ua:
            browser = name
            break
    
    # OS detection
    os_info = "Unknown OS"
    if 'windows' in ua:
        os_info = "Windows"
    elif 'macintosh' in ua or 'mac os x' in ua:
        os_info = "macOS"
    elif 'linux' in ua:
        os_info = "Linux"
    elif 'android' in ua:
        os_info = "Android"
    elif 'iphone' in ua or 'ipad' in ua:
        os_info = "iOS"
    
    # Device type
    device = "Desktop"
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        device = "Mobile"
    elif 'tablet' in ua or 'ipad' in ua:
        device = "Tablet"
    
    return f"{browser} on {os_info} ({device})"


async def send_login_notification_email(email: str, username: str, ip_address: str, user_agent: str = None):
    """Send login notification email with IP address and browser/device info"""
    
    # Parse user agent for browser/device info
    browser_info = "Unknown"
    if user_agent:
        browser_info = parse_user_agent(user_agent)
    
    subject = "New Login to Your FacialDerma AI Account"
    html_body = f"""
    <html>
        <body>
            <h2>New Login Detected</h2>
            <p>Hello {username},</p>
            <p>We detected a new login to your FacialDerma AI account.</p>
            <p><strong>IP Address:</strong> {ip_address}</p>
            <p><strong>Time:</strong> Just now</p>
            <p><strong>Browser/Device:</strong> {browser_info}</p>
            <br>
            <p>If this wasn't you, please secure your account immediately.</p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(email, subject, html_body)
