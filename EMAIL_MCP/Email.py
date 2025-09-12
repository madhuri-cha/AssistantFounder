import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(subject, body, to_email):
    from_email = os.getenv('APP_EMAIL')
    from_password = os.getenv('APP_PASSCODE')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(from_email, from_password)
            smtp.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    subject = "Test Email"
    body = "This is a test email sent using environment variables."
    to_email = "dumbreprajwal@gmail.com"

    send_email(subject, body, to_email)
