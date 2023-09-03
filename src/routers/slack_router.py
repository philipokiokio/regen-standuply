from fastapi import APIRouter
from typing import Dict, Union
from src.models.schemas import SlackEvent
from src.app.redis_cache import redis_client
from src.app.utils.slack_messenger import (
    slack_dm,
    slack_messenger,
    get_last_bot_message,
    QUESTION_DICT,
    SlackBot,
)
from src.app.celery_jobs import (
    automated_slack_message,
    slash_command_hack,
    second_question_task,
    third_question_task,
    success_standup_complete,
)


standup_bot_router = APIRouter(prefix="/api/standup", tags=["Standup Slack Bot"])


@standup_bot_router.post("/manual/stand-up/", status_code=200)
async def auto_with_endpoint_standup():
    automated_slack_message.delay()
    return {}


@standup_bot_router.post("/stand-up/", status_code=200)
async def standup_data(slash_data: Union[dict, str]):
    data_dict = {}
    for data_ in [data.split("=") for data in slash_data.split("&")]:
        data_dict[data_[0]] = data_[-1]
    slash_command_hack.delay(data_dict)
    resp = SlackBot("Enterscale Standup").get_message_payload(
        "Stand Up Messages Queued."
    )
    return resp


def standup_key_generator(message: str):
    question_index: Union[int, None] = None
    if message.startswith("1"):
        question_index = 0
        message = message.split("1")

    elif message.startswith("2"):
        question_index = 1
        message = message.split("2")

    elif message.startswith("3"):
        question_index = 2
        message = message.split("3")
    return question_index, message[-1].strip()


@standup_bot_router.post("/stand-up/event/", status_code=200)
def stand_up_events(data: Union[SlackEvent, Dict, None] = None):
    if type(data) == SlackEvent:
        return {"challenge": data.challenge}
        # Generate Cache Key
    if data["event"].get("client_msg_id") and data["event"]["user"] != "U05DN36GJH2":
        value = redis_client.get(data["event_id"])
        if not value:
            redis_client.set(data["event_id"], data["event_id"], ex=300)
            message: str = data["event"]["text"]
            question_key = get_last_bot_message(data["event"]["user"])
            processed_question = question_key["text"]
            check = QUESTION_DICT.get(processed_question)
            if type(check) == int:
                standup_key = f"{data['event']['user']}-{check}"
                value = redis_client.get(standup_key)
                if not value:
                    redis_client.set(standup_key, message, ex=3600)
                if value:
                    redis_client.set(standup_key, message, ex=3600)
                data_dict = {"user_id": data["event"]["user"]}
                if check == 0:
                    second_question_task.delay(data_dict)
                elif check == 1:
                    third_question_task.delay(data_dict)
                elif check == 2:
                    success_standup_complete.delay(data_dict)

    return {"staus": 200}
