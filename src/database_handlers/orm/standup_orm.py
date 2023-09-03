from sqlalchemy.orm import Session, load_only
from src.database_handlers.standup_model import Standup
from datetime import date
from typing import List


class StandupRepo:
    def __init__(self, db) -> None:
        self.db: Session = db

    def add_standup(self, data: dict):
        standup = Standup(**data)
        self.db.add(standup)
        self.db.commit()

    def get_by_date(self, date_: date, user_id: bool = False):
        loader = [
            Standup.yesterday_goal,
            Standup.plans_for_today,
            Standup.blockers,
            Standup.member_name,
            Standup.member_email,
        ]
        if user_id:
            loader.append(Standup.user_id)
        return (
            self.db.query(Standup)
            .filter(Standup.date_created == date_)
            .options(load_only(*loader))
            .all()
        )

    def get_for_user(self, user_uid: str):
        return (
            self.db.query(Standup)
            .filter(Standup.date_created == date.today(), Standup.user_id == user_uid)
            .first()
        )

    def get_singleton_by_date(self, date_: date, user_id: str):
        return (
            self.db.query(Standup)
            .filter(Standup.date_created == date_, Standup.user_id == user_id)
            .first()
        )

    def get_user_all_by_date(self, date_: date, user_id: str, mail_data: bool = False):
        loader = []
        if mail_data:
            loader = [
                Standup.yesterday_goal,
                Standup.plans_for_today,
                Standup.blockers,
                Standup.member_name,
                Standup.member_email,
            ]
        return (
            self.db.query(Standup)
            .filter(Standup.date_created == date_, Standup.user_id == user_id)
            .options(load_only(*loader))
            .all()
        )

    def delete_all_data(self, standup_data: List[Standup]):
        for standup in standup_data:
            self.db.delete(standup)

        self.db.commit()

    def delete_singleton(self, standup_data: Standup):
        self.db.delete(standup_data)
        self.db.commit()


standup_repo = StandupRepo
