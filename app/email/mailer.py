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


async def send_review_request_email(
    dermatologist_email: str,
    dermatologist_name: str,
    patient_name: str,
    prediction_id: str
):
    """Send email notification to dermatologist when a review is requested"""
    subject = "New Review Request - FacialDerma AI"
    html_body = f"""
    <html>
        <body>
            <h2>New Review Request</h2>
            <p>Hello Dr. {dermatologist_name},</p>
            <p>You have received a new review request from <strong>{patient_name}</strong>.</p>
            <p><strong>Prediction ID:</strong> {prediction_id}</p>
            <br>
            <p>Please log in to your dashboard to review the case and provide your expert feedback.</p>
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
    html_body = f"""
    <html>
        <body>
            <h2>Expert Review Added</h2>
            <p>Hello {patient_name},</p>
            <p>Dr. <strong>{dermatologist_name}</strong> has added an expert review to your prediction.</p>
            <p><strong>Prediction ID:</strong> {prediction_id}</p>
            <br>
            <p>Please log in to your account to view the detailed feedback from our dermatologist.</p>
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
