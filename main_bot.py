import importlib.util
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Gerekli paketler ve ilgili pip paket isimleri
required_packages = {
    "telegram": "python-telegram-bot",
}

# Her bir paket için kontrol et ve gerekirse kur
for module_name, package_name in required_packages.items():
    if importlib.util.find_spec(module_name) is None:
        print(f"{module_name} modülü yüklü değil. {package_name} paketi kuruluyor...")
        install(package_name)

# Standart kütüphane modülleri
import threading
import time
import os
import signal
import smtplib
from email.message import EmailMessage
import asyncio

# Telegram modülleri
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)

# Bot token'ınızı burada belirtiyorsunuz.
TOKEN = "USE YOUR TELEGRAM BOT TOKEN"

# Global değişkenler
progress_count = 0         # Gönderilen mail sayısını takip eder
spam_total = 0             # Toplam gönderilecek mail sayısı
spam_thread = None         # Spam thread'i
spam_active = False        # Spam işleminin aktif olup olmadığını gösterir
start_time = time.time()     # Botun başlangıç zamanı
logs_data = []             # Örnek log verisi

default_config = {
    "GMAIL_ADDRESS": "use your gmail address",
    "GMAIL_APP_PASSWORD": "USE YOUR GMAİL app PASS ",
    "SPAM_COUNT_DEFAULT": 10
}

# Konuşma aşamaları için sabitler
EMAIL, SUBJECT, BODY, COUNT = range(4)

# --- Spam gönderim fonksiyonu (arka plan thread'inde çalışır) ---
def spam_send(target, subject, body, count):
    global progress_count, spam_active, logs_data
    progress_count = 0
    spam_active = True

    msg = EmailMessage()
    msg['From'] = default_config["GMAIL_ADDRESS"]
    msg['To'] = target
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(default_config["GMAIL_ADDRESS"], default_config["GMAIL_APP_PASSWORD"])
            for i in range(count):
                # Spam işlemi durdurulduysa döngüden çık
                if not spam_active:
                    logs_data.append("Spam işlemi kullanıcı tarafından durduruldu.")
                    break
                server.send_message(msg)
                progress_count += 1
                logs_data.append(f"[{i+1}] Mail gönderildi: {target}")
                # Gönderimler arasında kısa bir gecikme (örneğin 1 saniye)
                time.sleep(1)
        logs_data.append("✅ Tüm mailler gönderildi.")
    except Exception as e:
        logs_data.append(f"❌ Hata oluştu: {e}")
    finally:
        spam_active = False

# --- Asenkron olarak ilerleme güncellemesi gönderen fonksiyon ---
async def update_progress(chat_id, context: ContextTypes.DEFAULT_TYPE, total):
    global progress_count, spam_active
    message = None
    while spam_active or progress_count < total:
        update_text = f"Şu ana kadar {progress_count} adet mail gönderildi."
        if message is None:
            message = await context.bot.send_message(chat_id, update_text)
        else:
            try:
                await context.bot.edit_message_text(
                    update_text, chat_id=chat_id, message_id=message.message_id
                )
            except Exception:
                message = await context.bot.send_message(chat_id, update_text)
        await asyncio.sleep(5)
    final_text = f"İşlem tamamlandı. Toplam {progress_count} adet mail gönderildi."
    await context.bot.send_message(chat_id, final_text)

# --- Komut Fonksiyonları ---
# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! Kullanabileceğin komutlar:\n"
        "/start - Başlangıç mesajı\n"
        "/help - Yardım\n"
        "/about - Bot hakkında bilgi\n"
        "/spam - Spam başlatır\n"
        "/status - Spam işleminin durumunu kontrol et\n"
        "/stop - Aktif spam işlemini durdur\n"
        "/logs - Logları gösterir\n"
        "/config - Bot ayarlarını görüntüler/günceller\n"
        "/schedule - Spam işlemini planlar\n"
        "/test - SMTP ve spam modülünü test eder\n"
        "/feedback - Geri bildirim gönderir\n"
        "/stats - İstatistikleri gösterir\n"
        "/info - Sistem ve kaynak bilgileri\n"
        "/restart - Botu yeniden başlatır\n"
        "/clearlogs - Logları temizler\n"
        "/uptime - Botun çalışma süresini gösterir\n"
        "/setdefault - Varsayılan ayarları belirler\n"
        "/monitor - Sistem kaynaklarını izler\n"
        "/version - Versiyon bilgisini gösterir\n"
        "/support - Destek bilgilerini sunar"
    )

# /help komutu
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📬 *Komutlar Listesi:*\n\n"
        "/start - Başlangıç mesajı\n"
        "/help - Yardım\n"
        "/about - Bot hakkında bilgi\n"
        "/spam - Spam başlatır\n"
        "/status - Spam işleminin durumunu kontrol et\n"
        "/stop - Aktif spam işlemini durdur\n"
        "/logs - Logları gösterir\n"
        "/config - Bot ayarlarını görüntüler/günceller\n"
        "/schedule - Spam işlemini planlar\n"
        "/test - SMTP ve spam modülünü test eder\n"
        "/feedback - Geri bildirim gönderir\n"
        "/stats - İstatistikleri gösterir\n"
        "/info - Sistem ve kaynak bilgileri\n"
        "/restart - Botu yeniden başlatır\n"
        "/clearlogs - Logları temizler\n"
        "/uptime - Botun çalışma süresini gösterir\n"
        "/setdefault - Varsayılan ayarları belirler\n"
        "/monitor - Sistem kaynaklarını izler\n"
        "/version - Versiyon bilgisini gösterir\n"
        "/support - Destek bilgilerini sunar"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# /about komutu
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "Bu bot spam işlemleri yapmak için geliştirilmiştir.\n"
        "Geliştirici: [Adınız]\n"
        "Versiyon: 1.0.0\n"
        "Not: Bu bot sadece test amaçlı kullanılmalıdır."
    )
    await update.message.reply_text(about_text)

# /spam komutu (konuşma başlatır)
async def spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📨 Hedef mail adresini yaz:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["target_email"] = update.message.text
    await update.message.reply_text("✉️ Konu başlığını yaz:")
    return SUBJECT

async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["subject"] = update.message.text
    await update.message.reply_text("💬 Mesaj içeriğini yaz:")
    return BODY

async def get_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["body"] = update.message.text
    await update.message.reply_text("🔢 Kaç adet mail gönderilsin? (Sadece sayı giriniz)")
    return COUNT

async def get_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_thread, spam_total
    try:
        count = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Hata: Lütfen geçerli bir sayı giriniz.")
        return COUNT

    spam_total = count
    target = context.user_data["target_email"]
    subject = context.user_data["subject"]
    body = context.user_data["body"]

    await update.message.reply_text("🚀 Spam işlemi başlatılıyor...")

    # Spam işlemini ayrı bir thread'de çalıştırıyoruz.
    spam_thread = threading.Thread(target=spam_send, args=(target, subject, body, count))
    spam_thread.start()

    # Arka planda, spam ilerlemesini her 5 saniyede bir güncelleyen asenkron task başlatıyoruz.
    asyncio.create_task(update_progress(update.message.chat_id, context, count))
    return ConversationHandler.END

# /status komutu
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if spam_active:
        await update.message.reply_text("Spam işlemi şu an aktif.")
    else:
        await update.message.reply_text("Aktif spam işlemi bulunmuyor.")

# /stop komutu
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_thread, spam_active
    if spam_active and spam_thread and spam_thread.is_alive():
        try:
            # spam_send içindeki döngüde kontrol edilen spam_active bayrağını False yapıyoruz.
            spam_active = False
            await update.message.reply_text("Aktif spam işlemi durduruluyor...")
        except Exception as e:
            await update.message.reply_text(f"Hata: {e}")
    else:
        await update.message.reply_text("Durdurulacak aktif bir spam işlemi bulunmuyor.")

# /logs komutu
async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if logs_data:
        await update.message.reply_text("\n".join(logs_data))
    else:
        await update.message.reply_text("Hiç log kaydı bulunmuyor.")

# /config komutu
async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config_text = "Bot Ayarları:\n"
    for key, value in default_config.items():
        config_text += f"{key}: {value}\n"
    await update.message.reply_text(config_text)

# /schedule komutu (placeholder)
async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Spam işlemini zamanlamak için gerekli özellik henüz eklenmedi.")

# /test komutu (SMTP ve spam modülünü test eder)
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(default_config["GMAIL_ADDRESS"], default_config["GMAIL_APP_PASSWORD"])
        await update.message.reply_text("SMTP ve spam modülü testi başarılı.")
    except Exception as e:
        await update.message.reply_text(f"Test başarısız: {e}")

# /feedback komutu
async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Geri bildiriminiz için teşekkürler! (Özellik henüz aktif değil)")

# /stats komutu
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats_text = f"Toplam gönderilen mail: {progress_count}\nHedef: {spam_total}\n"
    await update.message.reply_text(stats_text)

# /info komutu
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import sys
    info_text = f"Sistem Bilgileri:\nPython sürümü: {sys.version}\n"
    await update.message.reply_text(info_text)

# /restart komutu (placeholder)
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot yeniden başlatılıyor... (Özellik henüz aktif değil)")

# /clearlogs komutu
async def clearlogs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global logs_data
    logs_data = []
    await update.message.reply_text("Loglar temizlendi.")

# /uptime komutu
async def uptime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime_seconds = int(time.time() - start_time)
    await update.message.reply_text(f"Botun çalışma süresi: {uptime_seconds} saniye.")

# /setdefault komutu (placeholder)
async def setdefault_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Varsayılan ayarlar güncellendi. (Özellik henüz aktif değil)")

# /monitor komutu (placeholder)
async def monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sistem kaynakları izleniyor: CPU, Bellek vb. (Özellik henüz aktif değil)")

# /version komutu
async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Versiyonu: 1.0.0\nDeğişiklikler: İlk sürüm")

# /support komutu
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_text = (
        "Destek:\n"
        "Herhangi bir sorun için lütfen geliştirici ile iletişime geçin.\n"
        "Email: support@example.com\n"
        "SSS sayfası: https://example.com/support"
    )
    await update.message.reply_text(support_text)

# /cancel komutu (konuşma iptali)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 İşlem iptal edildi.")
    return ConversationHandler.END

# --- Main ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("spam", spam_command)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_subject)],
            BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_body)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("config", config_command))
    app.add_handler(CommandHandler("schedule", schedule_command))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("restart", restart_command))
    app.add_handler(CommandHandler("clearlogs", clearlogs_command))
    app.add_handler(CommandHandler("uptime", uptime_command))
    app.add_handler(CommandHandler("setdefault", setdefault_command))
    app.add_handler(CommandHandler("monitor", monitor_command))
    app.add_handler(CommandHandler("version", version_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("cancel", cancel))

    app.run_polling()

if __name__ == "__main__":
    main()
