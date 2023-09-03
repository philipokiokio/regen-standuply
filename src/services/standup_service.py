from fastapi import UploadFile
from src.app.redis_cache import redis_client
from datetime import date, datetime
from src.enterscale_slack.slack_messenger import (
    get_all_members,
    slack_dm,
    standup_web_client,
)
from src.enterscale_slack.standup_orm import standup_repo, Standup
from src.app.database import SessionLocal
import csv
import io


DAY_OF_THE_WEEK = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}
MONTH = {
    1: "January",
    2: "Febuary",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


QUESTIONS = [
    "What did you do yesterday?",
    "What do you plan on doing today?",
    "Okay, any blockers?",
]


def Save_to_DB(user_data: dict):
    for index in range(3):
        response = redis_client.get(f"{user_data['user_id']}-{index}")
        redis_client.set(name=f"{user_data['user_id']}-{index}", value="", ex=2)
        if index == 0:
            user_data["yesterday_goal"] = response.decode("utf-8")

        elif index == 1:
            user_data["plans_for_today"] = response.decode("utf-8")

        elif index:
            user_data["blockers"] = (
                None
                if response == " " or response is None
                else response.decode("utf-8")
            )

    user_data["day_of_the_week"] = DAY_OF_THE_WEEK[date.today().isoweekday()]
    user_data["date_created"] = date.today()

    with SessionLocal() as db:
        standup_repo(db).add_standup(user_data)


def Get_By_Date(user_id: str):
    with SessionLocal() as db:
        data = standup_repo(db).get_singleton_by_date(
            user_id=user_id, date_=date.today()
        )
    return data


def get_user_date(user_id: str):
    with SessionLocal() as db:
        data = standup_repo(db).get_singleton_by_date(
            date_=date.today(),
            user_id=user_id,
        )
    return data


def Delete_Standup_Data(data: Standup):
    with SessionLocal() as db:
        standup_repo(db).delete_singleton(data)


def delete_all_stand_up_data_for_the_week():
    monday = date.today().day - 4

    with SessionLocal() as db:
        for step in range(5):
            today = str(date.today())[:-2]
            date_of_week = f"{today}{str(monday +step)}"
            stand_up_data = standup_repo(db).get_by_date(date_=date_of_week)
            if stand_up_data:
                standup_repo(db).delete_all_data(standup_data=stand_up_data)


def send_users_end_of_week_report(user_id: str):
    day_collection = []

    with SessionLocal() as session:
        monday = date.today().day - 4

        for _ in range(5):
            today = str(date.today())[0:-2]
            print(today, monday)
            data_per_day = standup_repo(session).get_user_all_by_date(
                date_=today + str(monday), user_id=user_id, mail_data=True
            )
            print(data_per_day)
            if not data_per_day:
                day_collection += data_per_day
            else:
                data_per_day__ = []
                for data_per_day_ in data_per_day:
                    data_per_day_ = data_per_day_.__dict__
                    del data_per_day_["_sa_instance_state"]
                    del data_per_day_["id"]
                    data_per_day__.append(data_per_day_)
                day_collection += data_per_day__
            monday += 1

    return write_data_to_csv(day_collection)


def send_end_of_week_report():
    day_collection = []

    with SessionLocal() as session:
        monday = date.today().day - 4

        for _ in range(5):
            today = str(date.today())[0:-2]
            data_per_day = standup_repo(session).get_by_date(today + str(monday))
            if not data_per_day:
                day_collection += data_per_day
            else:
                data_per_day__ = []
                for data_per_day_ in data_per_day:
                    data_per_day_ = data_per_day_.__dict__
                    del data_per_day_["_sa_instance_state"]
                    del data_per_day_["id"]
                    data_per_day__.append(data_per_day_)
                day_collection += data_per_day__
            monday += 1

    return write_data_to_csv(day_collection)


def write_data_to_csv(data: list):
    if not data:
        return None

    file: io.StringIO = io.StringIO()
    fieldnames = [
        "plans_for_today",
        "yesterday_goal",
        "blockers",
        "member_name",
        "member_email",
    ]
    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=",")
    writer.writeheader()
    for stand_up_data in data:
        writer.writerow(stand_up_data)
    file.seek(0)
    return [UploadFile(filename="end_of_week_summary.csv", file=file)]


def daily_report_for_specified_channel(channel: str):
    target_channel = standup_web_client.conversations_info(channel=channel)

    with SessionLocal() as session:
        standup_data_for_today = standup_repo(session).get_by_date(
            date.today(), user_id=True
        )

    root_message = slack_dm(
        message=f"Summary for {DAY_OF_THE_WEEK[date.today().isoweekday()]}, {str(date.today().day)} {MONTH[date.today().month]}",
        people_id=f"#{target_channel['channel']['name']}",
        standup=True,
    )
    if not standup_data_for_today:
        message = "No Standup Message Recorded Today"

        slack_dm(
            message=message,
            people_id=f"#{target_channel['channel']['name']}",
            standup=True,
            thread_time_stamp=root_message["ts"],
        )

    else:
        for data_point in standup_data_for_today:
            data_point: Standup
            message = f"*{QUESTIONS[0]}*\n{data_point.yesterday_goal}\n* {QUESTIONS[1]}*\n{data_point.plans_for_today}\n* {QUESTIONS[2]}*\n{data_point.blockers}"
            slack_user = standup_web_client.users_info(user=data_point.user_id)
            slack_dm(
                message=message,
                people_id=f"#{target_channel['channel']['name']}",
                standup=True,
                thread_time_stamp=root_message["ts"],
                username=slack_user["user"]["profile"]["display_name"],
                image_url=slack_user["user"]["profile"]["image_original"],
            )
        all_members = get_all_members()
        for user in all_members:
            todays_data = standup_repo(session).get_for_user(user_uid=user)
            if todays_data is None:
                slack_user = standup_web_client.users_info(user=user)
                message = (
                    f"* {QUESTIONS[0]}*\n\n* {QUESTIONS[1]}*\n\n* {QUESTIONS[2]}*\n\n"
                )

                slack_dm(
                    message=message,
                    people_id=f"#{target_channel['channel']['name']}",
                    standup=True,
                    thread_time_stamp=root_message["ts"],
                    username=slack_user["user"]["profile"]["display_name"],
                    image_url=slack_user["user"]["profile"]["image_original"],
                )
