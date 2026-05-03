"""
Servicio de envío de correos vía SMTP.
Credenciales configuradas en el archivo .env
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM, SMTP_USE_TLS, APP_URL
)

logger = logging.getLogger(__name__)


def _send(to_address: str, subject: str, html_body: str, text_body: str = ""):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_FROM
    msg["To"]      = to_address

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_address], msg.as_bytes())
        server.quit()
        logger.info("Mail enviado a %s — %s", to_address, subject)
    except Exception as exc:
        logger.error("Error al enviar mail a %s: %s", to_address, exc)
        raise


def send_password_reset(to_address: str, username: str, reset_token: str):
    reset_link = f"{APP_URL}/frontend/index.html?reset={reset_token}"
    subject = "Restablecer contraseña — MuniMood"

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto">
      <div style="background:#1a3a5c;padding:20px;border-radius:8px 8px 0 0">
        <h1 style="color:#fff;margin:0;font-size:22px">🌡️ MuniMood</h1>
        <p style="color:#a8c8e8;margin:4px 0 0">Termómetro Político Municipal</p>
      </div>
      <div style="background:#f9f9f9;padding:30px;border:1px solid #ddd">
        <p>Hola <strong>{username}</strong>,</p>
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <p>Hacé clic en el botón para continuar:</p>
        <p style="text-align:center;margin:30px 0">
          <a href="{reset_link}"
             style="background:#1a3a5c;color:#fff;padding:14px 28px;text-decoration:none;
                    border-radius:6px;font-size:16px;font-weight:bold">
            Restablecer contraseña
          </a>
        </p>
        <p style="font-size:13px;color:#666">
          Este enlace vence en 1 hora.<br>
          Si no solicitaste este cambio, ignorá este mensaje.
        </p>
        <p style="font-size:13px;color:#999">
          O copiá este link en tu navegador:<br>
          <a href="{reset_link}" style="color:#1a3a5c">{reset_link}</a>
        </p>
      </div>
      <div style="background:#eee;padding:12px;text-align:center;font-size:11px;color:#999;border-radius:0 0 8px 8px">
        MuniMood — Sistema de Gestión Municipal
      </div>
    </body></html>
    """
    text_body = (
        f"Hola {username},\n\n"
        f"Para restablecer tu contraseña visitá:\n{reset_link}\n\n"
        "Este enlace vence en 1 hora.\n"
    )
    _send(to_address, subject, html_body, text_body)
