from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import categories, months, account, purchases, reports, income

app = FastAPI(title="Budget Pilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router, prefix="/api/v1")
app.include_router(months.router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")
app.include_router(purchases.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(income.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
