from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from src.app.database import Base
from sqlalchemy import Column, TIMESTAMP, text


class AbstractBase(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date_created = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def as_dict(self):
        return {field.name: getattr(self, field.name) for field in self.__table__.c}
