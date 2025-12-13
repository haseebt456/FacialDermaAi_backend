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
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
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
    login_link = f"{settings.FRONTEND_URL}/login"
    html_body = f"""
    <html>
        <body>
            <h2>Welcome to FacialDerma AI, {username}!</h2>
            <p>Thank you for registering with us. We're excited to have you on board.</p>
            <p>You can now log in and start using our facial dermatology AI services.</p>
            <p><a href="{login_link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">Click here to login</a></p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(email, subject, html_body)


async def send_verification_email(email: str, username: str, verification_token: str):
    """Send email verification link to user"""
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    
    subject = "Verify Your Email - FacialDerma AI"
    html_body = f"""
    <html>
        <body>
            <h2>Welcome to FacialDerma AI, {username}!</h2>
            <p>Thank you for registering. Please verify your email address to activate your account.</p>
            <br>
            <p><strong>Click the link below to verify your email:</strong></p>
            <p><a href="{verification_link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <br>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{verification_link}</p>
            <br>
            <p><small>This link will expire in {settings.VERIFICATION_TOKEN_EXPIRY_MINUTES} minutes.</small></p>
            <br>
            <p>If you didn't create an account, please ignore this email.</p>
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
    profile_link = f"{settings.FRONTEND_URL}/Profile"
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
            <p><a href="{profile_link}" style="display: inline-block; padding: 10px 20px; background-color: #dc2626; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">Review Account Security</a></p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(email, subject, html_body)


async def send_review_request_email(
    dermatologist_email: str,
    dermatologist_name: str,
    patient_name: str,
    prediction_id: str,
    message: str = None
):
    """Send email notification to dermatologist when a review is requested"""
    subject = "New Review Request - FacialDerma AI"
    dashboard_link = f"{settings.FRONTEND_URL}/Dermatologist"
    message_html = f"<p><strong>Patient Message:</strong> {message}</p>" if message else ""
    html_body = f"""
    <html>
        <body>
            <h2>New Review Request</h2>
            <p>Hello Dr. {dermatologist_name},</p>
            <p>You have received a new review request from <strong>{patient_name}</strong>.</p>
            <p><strong>Prediction ID:</strong> {prediction_id}</p>
            {message_html}
            <br>
            <p>Please log in to your dashboard to review the case and provide your expert feedback.</p>
            <p><a href="{dashboard_link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">Click here to view the request</a></p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(dermatologist_email, subject, html_body)


async def send_review_submitted_email(
    patient_email: str,
    patient_name: str,
    dermatologist_name: str,
    prediction_id: str
):
    """Send email notification to patient when dermatologist submits a review"""
    subject = "Expert Review Added - FacialDerma AI"
    profile_link = f"{settings.FRONTEND_URL}/Profile"
    html_body = f"""
    <html>
        <body>
            <h2>Expert Review Added</h2>
            <p>Hello {patient_name},</p>
            <p>Dr. <strong>{dermatologist_name}</strong> has added an expert review to your prediction.</p>
            <p><strong>Prediction ID:</strong> {prediction_id}</p>
            <br>
            <p>Please log in to your account to view the detailed feedback from our dermatologist.</p>
            <p><a href="{profile_link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">View Review Details</a></p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(patient_email, subject, html_body)


async def send_review_rejected_email(
    patient_email: str,
    patient_name: str,
    dermatologist_name: str,
    prediction_id: str,
    reason: str
):
    """Send email notification to patient when dermatologist rejects a review request"""
    subject = "Review Request Rejected - FacialDerma AI"
    profile_link = f"{settings.FRONTEND_URL}/dashboard"
    html_body = f"""
    <html>
        <body>
            <h2>Review Request Update</h2>
            <p>Hello {patient_name},</p>
            <p>Dr. <strong>{dermatologist_name}</strong> has rejected your review request.</p>
            <p><strong>Prediction ID:</strong> {prediction_id}</p>
            <p><strong>Reason:</strong> {reason}</p>
            <br>
            <p>You can request another dermatologist if needed.</p>
            <p><a href="{dashboard_link}" style="display: inline-block; padding: 10px 20px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">Request Another Dermatologist</a></p>
            <br>
            <p>Best regards,<br>The FacialDerma AI Team</p>
        </body>
    </html>
    """
    await send_email(patient_email, subject, html_body)


async def send_otp_email(email: str, username: str, otp: str):
    """Send OTP email for password reset"""
    
    # Development mode: Skip email and log OTP
    if settings.SKIP_EMAIL:
        print("\n" + "=" * 60)
        print("🔧 DEVELOPMENT MODE - EMAIL SKIPPED")
        print(f"📧 Email: {email}")
        print(f"👤 Username: {username}")
        print(f"🔐 OTP CODE: {otp}")
        print(f"⏰ Valid for: 10 minutes")
        print("=" * 60 + "\n")
        logger.info(f"DEV MODE: OTP for {email} is {otp}")
        return
    
    subject = "Password Reset OTP - FacialDerma AI"
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #2563eb; margin-bottom: 20px;">Password Reset Request</h2>
                <p>Hello <strong>{username}</strong>,</p>
                <p>You requested to reset your password for your FacialDerma AI account.</p>
                <p>Your One-Time Password (OTP) is:</p>
                <div style="background-color: #eff6ff; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #1e40af; letter-spacing: 8px; margin: 0; font-size: 36px;">{otp}</h1>
                </div>
                <p style="color: #dc2626; font-weight: bold;">⏰ This OTP will expire in 10 minutes.</p>
                <p>If you didn't request this password reset, please ignore this email or contact support if you have concerns.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px;">Best regards,<br>The FacialDerma AI Team</p>
            </div>
        </body>
    </html>
    """
    await send_email(email, subject, html_body)
