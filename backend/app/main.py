"""FastAPI application composition root."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1.controllers.health import router as health_router
from app.api.v1.controllers.papers import router as papers_router
from app.api.v1.controllers.rubrics import router as rubrics_router
from app.api.v1.controllers.reviews import router as reviews_router
from app.core.errors import DomainError


def register_error_handlers(application: FastAPI) -> None:
    """Map domain failures to the documented REST error shape."""

    @application.exception_handler(DomainError)
    async def handle_domain_error(_request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "detail": exc.detail},
        )

app = FastAPI(title="Evidence Grounded Paper Review", version="0.1.0")
register_error_handlers(app)
app.include_router(health_router)
app.include_router(papers_router)
app.include_router(rubrics_router)
app.include_router(reviews_router)

