import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sendgrid_email(to_email, subject, plain_message, html_message=None):
    """
    Send email using SendGrid Web API (works on Render)
    Supports both plain text and HTML templates
    """
    try:
        # Create the email message
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=to_email,
            subject=subject
        )

        # Add plain text content (FIXED: Use Content class correctly)
        message.add_content(Content("text/plain", plain_message))

        # Add HTML content if provided (FIXED: Use Content class correctly)
        if html_message:
            message.add_content(Content("text/html", html_message))

        # Send the email
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"SendGrid email sent successfully to {to_email}. Status: {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"SendGrid email failed for {to_email}: {str(e)}")
        return False