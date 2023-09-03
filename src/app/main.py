from src.app.main_service import main_service
from fastapi import status


# INTIIALIZATION OF THE FASTAPI APPLICATION
app = main_service.init_app()


# ROOT ENDPOINT
@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "Oma the server", "docs": "/docs"}
