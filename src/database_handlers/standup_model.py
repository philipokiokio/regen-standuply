from sqlalchemy import Column, String, Integer, Date
from src.app.database import Base


class Standup(Base):
    __tablename__ = "standup"
    id = Column(Integer, primary_key=True)
    yesterday_goal = Column(String, nullable=True)
    plans_for_today = Column(String, nullable=False)
    blockers = Column(String, nullable=True)
    day_of_the_week = Column(String, nullable=False)
    member_name = Column(String, nullable=False)
    member_email = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    date_created = Column(Date, nullable=False)
