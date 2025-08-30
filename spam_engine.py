import sys
import smtplib
from email.message import EmailMessage

# Dikkat: Bu bilgileri gerçek projelerde doğrudan kod içine yazmak güvenlik açığı oluşturur.
GMAIL_ADDRESS = "jacksonstormishere@gmail.com"
GMAIL_APP_PASSWORD = "skhdkbuaguqxttqm"

def spam(target, subject, body, count):
    msg = EmailMessage()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = target
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            for i in range(count):
                server.send_message(msg)
                print(f"[{i+1}] Mail gönderildi: {target}")
        print("✅ Tüm mailler başarıyla gönderildi.")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Kullanım: python spam_engine.py <email> <subject> <body> <count>")
        sys.exit(1)

    target_email = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]
    try:
        count = int(sys.argv[4])
    except ValueError:
        print("Hata: count sayısal bir değer olmalıdır.")
        sys.exit(1)

    spam(target_email, subject, body, count)
