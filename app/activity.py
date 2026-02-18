import app.schemas as schemas
import app.models as models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter, Request
from app.database import get_db

router = APIRouter()


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.ActivityLogResponse
)
def create_activity_log(
    payload: schemas.ActivityLogCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No User with this id: `{payload.user_id}` found",
        )

    try:
        log_data = payload.dict()
        if log_data.get("ip_address") is None:
            log_data["ip_address"] = request.client.host if request.client else None

        new_log = models.ActivityLog(**log_data)
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the activity log.",
        ) from e

    log_schema = schemas.ActivityLogResponseSchema.from_orm(new_log)
    return schemas.ActivityLogResponse(Status=schemas.Status.Success, Log=log_schema)


@router.get(
    "/user/{userId}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ListActivityLogResponse,
)
def get_user_activity_logs(
    userId: str,
    db: Session = Depends(get_db),
    limit: int = 10,
    page: int = 1,
):
    skip = (page - 1) * limit

    logs = (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.user_id == userId)
        .order_by(models.ActivityLog.createdAt.desc())
        .limit(limit)
        .offset(skip)
        .all()
    )

    log_schemas = [schemas.ActivityLogResponseSchema.from_orm(log) for log in logs]
    return schemas.ListActivityLogResponse(
        status=schemas.Status.Success,
        results=len(log_schemas),
        logs=log_schemas,
    )


@router.get(
    "/{logId}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ActivityLogResponse,
)
def get_activity_log(logId: str, db: Session = Depends(get_db)):
    log = db.query(models.ActivityLog).filter(models.ActivityLog.id == logId).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No activity log with this id: `{logId}` found",
        )

    log_schema = schemas.ActivityLogResponseSchema.from_orm(log)
    return schemas.ActivityLogResponse(Status=schemas.Status.Success, Log=log_schema)
