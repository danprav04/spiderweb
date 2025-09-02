# app/__init__.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi import Request
from app.database import get_async_db
from app.config import Config
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(
        title="Spiderweb Service",
        description="Spiderweb Service API",
        version="1.0.0",
        openapi_url="/api/v1/openapi.json",
        # on_request_exception=handle_request_exception
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        error = jsonable_encoder({"error": "Validation Error", "details": exc.errors()})
        return JSONResponse(status_code=422, content=error)

    return app


app = create_app()
