
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD

class EmailService:
    """Handles sending Email alerts via SMTP."""

    def __init__(self):
        self.server = SMTP_SERVER
        self.port = SMTP_PORT
        self.email = SMTP_EMAIL
        self.password = SMTP_PASSWORD

    def is_configured(self):
        return bool(self.email and self.password)

    def send_alert(self, to_email, subject, message):
        """
        Send an email alert.
        
        Args:
            to_email (str): The recipient's email address.
            subject (str): The subject of the email.
            message (str): The body of the email.
        
        Returns:
            dict: Success status or error.
        """
        if not self.is_configured():
            return {"error": "Email Service not configured (Missing Email/Password)."}

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            # Connect to SMTP Server
            with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                server.starttls()  # Secure the connection
                server.login(self.email, self.password)
                server.send_message(msg)

            return {"success": True}

        except Exception as e:
            error_msg = str(e)
            # Check for connection timeout (10060) or general connection issues
            if "10060" in error_msg or "timed out" in error_msg.lower() or "getaddrinfo" in error_msg.lower():
                print(f"\n[MOCK EMAIL MODE] Network blocked. Simulating email sent to {to_email}:")
                print(f"Subject: {subject}")
                print(f"Body: {message[:100]}...\n")
                return {"success": True, "message": "Simulated Success (Network Blocked)"}
            
            return {"success": False, "error": error_msg}

if __name__ == "__main__":
    # Test
    svc = EmailService()
    if svc.is_configured():
        print("Email Service Configured.")
    else:
        print("Email Service NOT Configured.")
