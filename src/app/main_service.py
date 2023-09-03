from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.slack_router import standup_bot_router


class MainService:
    def cors_orgins(self) -> List:
        origin_list: List = ["*"]
        return origin_list

    def init_app(self) -> FastAPI:
        # Initialization of the FASTAPI APPLICATION
        app: FastAPI = FastAPI(
            title="StandUp Service",
            contact={
                "name": " Regen Standuply",
                "email": "philipokiokio@gmail.com",
            },
        )
        # CORS MIDDLEWARE MOUNTED ON THE APPLICATION
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_orgins(),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # MOUNTING ROUTERS

        app.include_router(standup_bot_router)

        return app


main_service = MainService()
