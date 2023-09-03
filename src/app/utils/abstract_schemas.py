from pydantic import BaseModel
from pydantic_settings import BaseSettings


# DTO MODEL
class AbstractModel(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True


# DTO RESPONSE MODEL
class ResponseModel(AbstractModel):
    message: str
    status: int


# SETTINGS FOR ABSTRACT SETTINGS
class AbstractSettings(BaseSettings):
    class Config:
        env_file = ".env"
