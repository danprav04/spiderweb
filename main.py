# app/__init__.py
from fastapi import FastAPI
from app.config import Config
from app.routes.coredevice import router as coredevice_router
from app.routes.coresite import router as coresite_router
from app.routes.link import router as link_router
from app.routes.network import router as network_router
from app.routes.site import router as site_router
from app.routes.user import router as user_router
from app.routes.alerts import router as alert_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Spiderweb Service",
    description="Spiderweb Service API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=False,
                   allow_methods=["*"],
                   allow_headers=["*"]
                   )


@app.get('/')
def init():
    return 'Works'


app.include_router(coredevice_router)
app.include_router(coresite_router)
app.include_router(link_router)
app.include_router(network_router)
app.include_router(site_router)
app.include_router(user_router)
app.include_router(alert_router)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=int(Config().PORT))
