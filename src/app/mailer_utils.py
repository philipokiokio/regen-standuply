from typing import List, Union

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from pathlib import Path
from src.app.config import mail_settings

# MAIL CONFIGURATION
conf = ConnectionConfig(
    MAIL_USERNAME=mail_settings.mail_username,
    MAIL_PASSWORD=mail_settings.mail_password,
    MAIL_FROM=mail_settings.mail_from,
    MAIL_PORT=mail_settings.mail_port,
    MAIL_SERVER=mail_settings.mail_server,
    MAIL_FROM_NAME=mail_settings.mail_from_name,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent.parent / "templates",
)


# SEND EMAILS
async def send_mail(
    mail_subject: str,
    recipient: List[EmailStr],
    data: Union[str, dict],
    attachments: list = [],
    template_name: str = None,
):
    mail_message = MessageSchema
    if type(data) == "str":
        mail_message = MessageSchema(
            subject=mail_subject,
            recipients=recipient,
            body=data,
            attachments=attachments,
            subtype=MessageType.html,
        )
    else:
        mail_message = MessageSchema(
            subject=mail_subject,
            recipients=recipient,
            template_body=data,
            attachments=attachments,
            subtype=MessageType.html,
        )
    fm = FastMail(conf)
    try:
        if template_name:
            await fm.send_message(mail_message, template_name=template_name)
        else:
            await fm.send_message(mail_message)
        return True
    except Exception:
        return False
