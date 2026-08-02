from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.demo_seed_service import ensure_demo,is_demo_user,restore_demo
router=APIRouter()
def enabled():
    if not get_settings().demo_mode: raise HTTPException(404,"Demo mode is disabled")
@router.post("/login")
async def login(db:Annotated[Session,Depends(get_db)]):
    enabled(); user,profile,_=ensure_demo(db);return {"access_token":create_access_token({"sub":user.id}),"token_type":"bearer","user":{"id":user.id,"name":user.name,"email":user.email,"is_demo":True},"active_profile_id":profile.id}
@router.post("/reset")
async def reset(db:Annotated[Session,Depends(get_db)],user:Annotated[User,Depends(get_current_user)]):
    enabled()
    if not is_demo_user(user): raise HTTPException(403,"This action is disabled for the demo account.")
    _,profile,_=restore_demo(db);return {"status":"reset","active_profile_id":profile.id,"message":"Demo data has been restored."}
