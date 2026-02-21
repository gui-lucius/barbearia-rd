# agendamentos/email_service.py

import os
import logging

import resend

logger = logging.getLogger(__name__)


def send_resend_email(*, to_email: str, subject: str, html: str, text: str = "") -> None:
    """
    Envia e-mail via Resend (API).
    Requer:
      - RESEND_API_KEY
      - DEFAULT_FROM_EMAIL (ex: 'Barbearia RD <onboarding@resend.dev>')
    """
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("DEFAULT_FROM_EMAIL", "").strip()

    if not api_key:
        raise RuntimeError("RESEND_API_KEY não configurada no ambiente.")
    if not from_email:
        raise RuntimeError("DEFAULT_FROM_EMAIL não configurada no ambiente.")
    if not to_email:
        raise ValueError("to_email vazio.")
    if not subject:
        raise ValueError("subject vazio.")
    if not html and not text:
        raise ValueError("É necessário informar html ou text.")

    # Resend precisa de texto ou html; se text vier vazio, manda um placeholder
    if not text:
        text = " "

    resend.api_key = api_key

    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html or f"<pre>{text}</pre>",
                "text": text,
            }
        )
        logger.info("✅ Resend: e-mail enviado para=%s assunto=%s", to_email, subject)
    except Exception:
        logger.exception("❌ Resend: falha ao enviar e-mail para=%s assunto=%s", to_email, subject)
        raise


def get_barbeiro_email() -> str:
    """
    Email do barbeiro que recebe notificações.
    Usa BARBEARIA_EMAIL (Railway Variables).
    """
    return os.getenv("BARBEARIA_EMAIL", "").strip()