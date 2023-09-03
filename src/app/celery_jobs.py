import json
from celery import Celery
from src.app.config import redis_settings
from httpx import Client
from time import sleep
from src.services.standup_service import (
    MONTH,
    Delete_Standup_Data,
    Get_By_Date,
    Save_to_DB,
    daily_report_for_specified_channel,
    delete_all_stand_up_data_for_the_week,
    send_end_of_week_report,
    get_user_date,
    send_users_end_of_week_report,
)
from src.app.utils.slack_messenger import (
    send_interactive_message,
    slack_dm,
    get_all_members,
    get_user_profile,
)
from celery.schedules import crontab
from asgiref.sync import async_to_sync
from datetime import date, datetime, timedelta

# MAIL CONFIGURATION
from pydantic import EmailStr
from typing import List
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pathlib import Path

from src.app.config import mail_settings
from src.app.redis_cache import redis_client
from src.app.database import SessionLocal
from typing import Union


# SEND EMAILS
async def send_mail(
    mail_subject: str, recipient: List[EmailStr], data: str, attachment: list = []
):
    mail_message = MessageSchema(
        subject=mail_subject,
        recipients=recipient,
        body=data,
        attachments=attachment,
        subtype=MessageType.html,
    )
    conf = ConnectionConfig(
        MAIL_USERNAME=mail_settings.mail_username,
        MAIL_PASSWORD=mail_settings.mail_password,
        MAIL_FROM="noreply@standuply.com",
        MAIL_PORT=mail_settings.mail_port,
        MAIL_SERVER=mail_settings.mail_server,
        MAIL_FROM_NAME="Regen Standuply",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(mail_message)
        return True
    except Exception:
        return False


app = Celery(
    "regen_standup",
    broker=f"redis://{redis_settings.host}:{redis_settings.port}/{redis_settings.db}",
    broker_connection_retry_on_startup=True,
)


req = Client()


# STANDUP BOT
@app.task
def round_up_daily_report():
    print("Sending report to the Annoucment Channel")
    ANNOUNCEMENT_ID = "C015SCP4U3G"
    daily_report_for_specified_channel(ANNOUNCEMENT_ID)


@app.task
def automated_slack_message():
    members = get_all_members()
    for member in members:
        start_standup.delay(member)


@app.task
def start_standup(member_id: str):
    automated_slash_command.delay({"user_id": member_id})


QUESTIONS = [
    "What did you do yesterday?",
    "What do you plan on doing today?",
    "Okay, any blockers?",
]


@app.task
def automated_slash_command(data_dict: dict):
    # check for data for today and delete it.
    data = Get_By_Date(data_dict["user_id"])
    if data:
        return

    slack_dm(
        message="Hi there, it's time to start the standup meeting. Please, answer these 3 questions.",
        people_id=data_dict["user_id"],
        standup=True,
    )
    first_question_task.delay(data_dict)


@app.task
def slash_command_hack(data_dict: dict):
    # check for data for today and delete it.
    data = Get_By_Date(data_dict["user_id"])
    print(data)
    if data:
        Delete_Standup_Data(data=data)

    slack_dm(
        message="Hi there, it's time to start the standup meeting. Please, answer these 3 questions.",
        people_id=data_dict["user_id"],
        standup=True,
    )
    first_question_task.delay(data_dict)


@app.task
def first_question_task(data_dict: dict):
    # Send standup questions via direct message

    # Send Question
    slack_dm(QUESTIONS[0], data_dict["user_id"], True)


@app.task
def second_question_task(data_dict: dict):
    # Send standup questions via direct message

    # Send Question
    slack_dm(QUESTIONS[1], data_dict["user_id"], True)


@app.task
def third_question_task(data_dict: dict):
    # Send standup questions via direct message

    # Send Question
    slack_dm(QUESTIONS[2], data_dict["user_id"], True)


@app.task
def success_standup_complete(data_dict: dict):
    slack_dm(message="Great, got it 🙌🏾", people_id=data_dict["user_id"], standup=True)

    user_info = get_user_profile(user_id=data_dict["user_id"])
    Save_to_DB(user_data=user_info)


@app.task
def mid_report_nudge():
    print("Mid Stand Up Report acknowledge")
    slack_members = get_all_members()
    for member in slack_members:
        data = get_user_date(user_id=member)
        if data is None:
            slack_dm(
                message="The standup is running. Please answer the questions in time 😩",
                people_id=member,
                standup=True,
            )


@app.task
def end_report_nudge_for_manual_filling():
    print("End Stand Up Report acknowledge")
    slack_members = get_all_members()
    for member in slack_members:
        data = get_user_date(member)
        if data is None:
            slack_dm(
                message="You're out of time. I'm wrapping up the report without your answers 😢",
                people_id=member,
                standup=True,
            )


@app.task
def end_of_week_report_for_user():
    print("End of the Week Report for Workspace Member")
    slack_users = get_all_members()
    for member in slack_users:
        mail_attachments = send_users_end_of_week_report(user_id=member)
        mail_email = get_user_date(user_id=member)
        if not mail_attachments:
            pass
        else:
            sender = async_to_sync(send_mail)(
                mail_subject=f"Standup Report results from {date.today().day} {MONTH[date.today().month]} {date.today().year}",
                recipient=[
                    mail_email.member_email,
                ],
                data="<p><h4>Hi!<h4><p><br><br>TGIF!<br><br><p>Here is the Standup report for all staff during the Week.<p><br><br><br><br>Enterscale's Bot",
                attachment=mail_attachments,
            )
            print(sender)
    print("Mail Sent")


@app.task
def end_of_week_report():
    print("End of the Week Report")
    mail_attachments = send_end_of_week_report()
    if not mail_attachments:
        return
    print("test")
    async_to_sync(send_mail)(
        mail_subject=f"Standup Report results from {date.today().day} {MONTH[date.today().month]} {date.today().year}",
        recipient=["leads@enterscale.com"],
        data="<p><h4>Hi!<h4><p><br><br>TGIF!<br><br><p>Here is the Standup report for all staff during the Week.<p><br><br><br><br>Enterscale's Bot",
        attachment=mail_attachments,
    )
    # Delete Record of the Week
    delete_all_stand_up_data_for_the_week()
    print("Mail Sent")


# Celery uses UTC timezone by default
app.add_periodic_task(
    crontab(minute="00", hour="8", day_of_week="mon,tue,wed,thu,fri"),
    automated_slack_message.s(),
    name="Stand Up Automation",
)
app.add_periodic_task(
    crontab(minute="30", hour="8", day_of_week="mon,tue,wed,thu,fri"),
    mid_report_nudge.s(),
    name="Mid Scheduled Report Check",
)
app.add_periodic_task(
    crontab(minute="00", hour="9", day_of_week="mon,tue,wed,thu,fri"),
    end_report_nudge_for_manual_filling.s(),
    name="End Scheduled Report Check",
)

app.add_periodic_task(
    crontab(minute="30", hour="9", day_of_week="mon,tue,wed,thu,fri"),
    round_up_daily_report.s(),
    name="Annoucement Summary",
)

app.add_periodic_task(
    crontab(minute="30", hour="15", day_of_week="fri"),
    end_of_week_report_for_user.s(),
    name="Stand Up End of Week Report For Users",
)

app.add_periodic_task(
    crontab(minute="00", hour="16", day_of_week="fri"),
    end_of_week_report.s(),
    name="Stand Up End of Week Report",
)
