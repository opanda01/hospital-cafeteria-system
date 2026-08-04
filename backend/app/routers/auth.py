from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_utils import create_access_token, verify_password
from app.database import get_db
from app.models import AdminUser
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminUser).where(AdminUser.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.aktif or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")
    tenant_id = str(user.tenant_id) if user.tenant_id else None
    token = create_access_token(user.email, tenant_id, user.role)
    return TokenResponse(access_token=token)
