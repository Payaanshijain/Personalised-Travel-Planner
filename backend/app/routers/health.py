from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
@router.get("/api/health", include_in_schema=False)
def health_check():
    return {
        "status": "ok",
        "message": "Backend is running. You can connect the frontend now.",
    }
