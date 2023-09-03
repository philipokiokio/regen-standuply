from src.app.utils.abstract_schemas import AbstractModel, ResponseModel


# SLACK EVENT VERIFY DATA
class SlackEvent(AbstractModel):
    token: str
    challenge: str
    type: str
