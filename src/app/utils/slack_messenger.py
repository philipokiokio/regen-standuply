from src.app.config import slack_settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
from src.app.redis_cache import redis_client

slack_web_client = WebClient(token=slack_settings.access_token)
standup_web_client = WebClient(token=slack_settings.standup_token)

QUESTION_DICT = {
    "What did you do yesterday?": 0,
    "What do you plan on doing today?": 1,
    "Okay, any blockers?": 2,
}


# Create the SLACKBOT Class
class SlackBot:
    # The constructor for the class. It takes the channel name
    def __init__(self, channel):
        self.channel = channel

    def send_message(self, message):
        text = message

        return {"type": "section", "text": {"type": "mrkdwn", "text": text}}

    # Craft and return the entire message payload as a dictionary.
    def get_message_payload(self, message):
        return {
            "channel": self.channel,
            "blocks": [
                self.send_message(message),
            ],
        }


# SLACK MESSENGER
def slack_messenger(message, channel_id: str):
    # Create a slack client
    try:
        channel = slack_web_client.conversations_info(channel=channel_id)
        if channel["ok"]:
            message += f"\nPosted in {channel['channel']['name']}"
    except SlackApiError:
        pass
    # Check if the API call was successful
    target_channel = slack_web_client.conversations_info(channel="C05AVMY45EX")
    slack_bot = SlackBot(f"#{target_channel['channel']['name']}")
    # Get the onboarding message payload
    message = slack_bot.get_message_payload(message)
    try:
        slack_web_client.chat_postMessage(**message)

    except SlackApiError:
        pass


# SLACK MESSENGER
def slack_dm(
    message,
    people_id: str,
    thread_time_stamp: str = None,
    username: str = None,
    image_url: str = None,
):
    # Create a slack client
    slack_bot = SlackBot(people_id)
    # Get the onboarding message payload

    message_ = slack_bot.get_message_payload(message)

    try:
        if username:
            return standup_web_client.chat_postMessage(
                **message_,
                thread_ts=thread_time_stamp or None,
                username=username,
                icon_url=image_url or None,
            )

        return standup_web_client.chat_postMessage(
            **message_,
            thread_ts=thread_time_stamp or None,
        )

    except SlackApiError:
        pass


def delete_standup_update(response_count: int, user_id: str):
    # Delete cached Response
    for count in range(response_count):
        redis_client.delete(name=user_id + f"-{count}")


def get_all_members():
    members = []
    try:
        response = standup_web_client.users_list()
        members = response["members"]
        members = [
            member["id"]
            for member in members
            if not member["is_bot"]
            and not member["deleted"]
            and member["id"] != "USLACKBOT"
        ]
    except Exception:
        pass

    return members


def get_user_profile(user_id):
    user_data = standup_web_client.users_profile_get(user=user_id)
    data = {}
    data["member_name"] = user_data["profile"]["real_name"]
    data["member_email"] = user_data["profile"]["email"]
    data["user_id"] = user_id
    return data


def get_last_bot_message(channel):
    dm_id = get_direct_message_id(channel)
    response = standup_web_client.conversations_history(channel=dm_id)
    if response["ok"]:
        messages = response["messages"]
        bot_messages = [message for message in messages if "bot_id" in message]
        if bot_messages:
            sorted_messages = sorted(bot_messages, key=lambda x: x["ts"], reverse=True)
            last_message = sorted_messages[0]
            if (
                last_message["text"]
                == "The standup is running. Please answer the questions in time :weary:"
            ):
                last_message = sorted_messages[1]
            return last_message


def get_direct_message_id(user_id):
    response = standup_web_client.conversations_open(users=[user_id])
    if response["ok"]:
        channel = response["channel"]
        direct_message_id = channel["id"]
        return direct_message_id
