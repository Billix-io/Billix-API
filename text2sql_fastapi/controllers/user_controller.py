from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import timedelta, datetime
from schemas.user_schemas import UserCreate, UserUpdate, UserLogin, UserBase,UserResponse, GoogleAuthModel
from database import get_session  # Adjust this import based on your project structure
from DAL_files.users_dal import UserDAL
from DAL_files.roles_dal import RoleDAL
from utils import verify_password, create_access_token, generate_passwd_hash
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from dependencies import RoleChecker, get_current_user, AccessTokenBearer
from redis_store import add_jti_to_blocklist, token_in_blocklist
import logging
from models.enums import RoleEnum

from pydantic import BaseModel, EmailStr

"""
User authentication and management endpoints for the FastAPI application.
Includes registration, login, Google OAuth, OTP, password reset, and user CRUD operations.
"""

auth_router = APIRouter()
user_service = UserDAL()
role_serivce = RoleDAL()

access_token_bearer=AccessTokenBearer()
role_checker = Depends(RoleChecker([RoleEnum.admin, RoleEnum.super_admin]))
REFRESH_TOKEN_EXPIRY = 2 

class SendOtpRequest(BaseModel):
    """
    Request schema for sending OTP to a user's email.
    """
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    """
    Request schema for verifying OTP sent to a user's email.
    """
    email: EmailStr
    otp_code: str

class PasswordResetRequest(BaseModel):
    """
    Request schema for initiating a password reset via email.
    """
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """
    Request schema for confirming password reset with OTP and new password.
    """
    email: EmailStr
    otp_code: str
    new_password: str

@auth_router.get("/all-users", response_model=list[UserResponse], dependencies=[role_checker])
async def get_all_users(session: AsyncSession = Depends(get_session)):
    """
    Retrieve all users. Requires admin or super_admin role.
    """
    users = await user_service.get_all_users(session)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

@auth_router.post("/google")
async def google_login(google_data: GoogleAuthModel, session: AsyncSession = Depends(get_session)):
    """
    Authenticate or register a user using Google OAuth and return tokens.
    """
    # 1. Verify the Google ID token and extract user info
    user_info = await user_service.verify_google_token(google_data.id_token)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")
    
    # Extract data from verified token
    google_id = user_info["sub"]  # Google's unique user ID
    email = user_info["email"]
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")

    # 2. Check if user already exists using google_id
    user = await user_service.get_user_by_google_id(google_id, session)
    
    if user is None:
        # Fallback: check if email exists already (to prevent duplicate accounts)
        user = await user_service.get_user_by_email(email, session)

    if user is None:
        # 3. Create new user
        user_create = UserCreate(
            email=email,
            first_name=first_name,
            last_name=last_name,
            google_id=google_id,
         
        )
        user = await user_service.create_user(user_create, session)

    # 4. Prepare user data for token generation
    user_data = {
        "email": user.email,
        "user_uid": str(user.uid),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "age": user.age
    }

    # 5. Generate tokens
    access_token = create_access_token(user_data=user_data)
    refresh_token = create_access_token(
        user_data=user_data,
        refresh=True,
        expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
    )

    return JSONResponse(
        content={
            "message": "Google login successful",
            "token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "email": user.email,
                "uid": str(user.uid),
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    )


@auth_router.post("/sign-up", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate,session: AsyncSession = Depends(get_session)):
    """
    Register a new user, send OTP, and return access token.
    """
    #check user Role exists
    role=await role_serivce.get_role_by_name("user",session)
    if not role:
        raise HTTPException(status_code=400, detail="Role 'user' does not exist add role")

    email=user.email
    # Check if email already exists 
    existing_user = await user_service.get_user_by_email(email, session)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = await user_service.create_user(user, session)
    if not created_user:
        raise HTTPException(status_code=400, detail="User creation failed")
    
    # Generate token
    access_token = create_access_token(
        user_data={
            "email": created_user.email,
            "user_id": str(created_user.user_id),  # Convert UUID to string
            "role_id": str(created_user.role_id)   # Convert UUID to string
        }
    )

    # Send OTP to user's email
    otp_code = user_service.generate_otp()
    await user_service.save_otp(created_user.email, otp_code, expiry_minutes=10, db_session=session)
    await user_service.send_otp_via_email(created_user.email, otp_code)
    
    return {
        "message": "User created successfully. OTP sent to email.",
        "user": {
            "user_id": str(created_user.user_id),  # Convert UUID to string
            "email": created_user.email,
            "first_name": created_user.first_name,
            "last_name": created_user.last_name
        },
        "token": access_token
    }

@auth_router.get("/logout")
async def logout_users(token_details: str = Depends(AccessTokenBearer())):
    """
    Logout the user by blacklisting the current JWT token.
    """
    jti = token_details["jti"]
    # Add the JTI to the blocklist with an expiry time
    await add_jti_to_blocklist(jti)
    # Optionally, you can also invalidate the refresh token if needed   
    return JSONResponse(content={"message": "Logout successful"},status_code=status.HTTP_200_OK)
    
@auth_router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: UserBase = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Get the current authenticated user's details.
    """
    user_id = current_user.user_id
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
    user = await user_service.get_user_by_id(user_id, session)
    return user

@auth_router.post("/sign-in")
async def login_users(login_data: UserLogin, session: AsyncSession = Depends(get_session)):
    """
    Authenticate a user with email and password, returning access (and optionally refresh) tokens.
    """
    email = login_data.email
    password = login_data.password
    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        password_valid = verify_password(password, user.password_hash)
        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_id": str(user.user_id),  # Convert UUID to string
                    "role_id": str(user.role_id)   # Convert UUID to string
                }
            )
            response_content = {
                "message": "Login successful",
                "token": access_token,
                "user": {
                    "email": user.email,
                    "user_id": str(user.user_id),  # Convert UUID to string
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                }
            }
            if login_data.remember_me:
                refresh_token = create_access_token(
                    user_data={
                        "email": user.email,
                        "user_id": str(user.user_id),  # Convert UUID to string
                        "role_id": str(user.role_id)   # Convert UUID to string
                    },
                    refresh=True,
                    expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
                )
                response_content["refresh_token"] = refresh_token
            return JSONResponse(content=response_content)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email or password")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found")

@auth_router.get("/{user_id}", response_model=UserBase)
async def get_user_by_id(user_id: str, session: AsyncSession = Depends(get_session)):
    print(type(user_id),"=====================")
    user = await user_service.get_user_by_id(user_id,session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@auth_router.post("/users/{user_id}/change-role/{new_role_id}")
async def change_user_role_endpoint(
    user_id: str,
    new_role_id: str,
    db_session: AsyncSession = Depends(get_session),
   
):
    try:
        updated_user = await user_service.change_user_role(user_id, new_role_id, db_session)
        return {"message": "User role updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@auth_router.get("/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str,session: AsyncSession = Depends(get_session)):
    print(email,"=====================")

    user = await user_service.get_user_by_email(email,session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@auth_router.put("/{user_id}", response_model=UserBase)
async def update_user(user_id: str, user_update: UserUpdate,  session: AsyncSession = Depends(get_session)):
    updated_user = await user_service.update_user(user_id, user_update,session)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@auth_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str,session: AsyncSession = Depends(get_session)):
    success = await user_service.delete_user(user_id,session)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@auth_router.post("/send-otp")
async def send_otp(request: SendOtpRequest, session: AsyncSession = Depends(get_session)):
    user = await user_service.get_user_by_email(request.email, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    otp_code = user_service.generate_otp()
    await user_service.save_otp(request.email, otp_code, expiry_minutes=10, db_session=session)
    await user_service.send_otp_via_email(request.email, otp_code)
    return {"message": "OTP sent to email"}

@auth_router.post("/verify-otp")
async def verify_otp(request: VerifyOtpRequest, session: AsyncSession = Depends(get_session)):
    user = await user_service.verify_otp(request.email, request.otp_code, session)
    return {"message": "User verified successfully", "is_verified": user.is_verified}

@auth_router.post("/password-reset/request")
async def request_password_reset(request: PasswordResetRequest, session: AsyncSession = Depends(get_session)):
    user = await user_service.get_user_by_email(request.email, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    otp_code = user_service.generate_otp()
    await user_service.save_otp(request.email, otp_code, expiry_minutes=10, db_session=session)
    await user_service.send_otp_via_email(request.email, otp_code)
    return {"message": "Password reset OTP sent to email"}

@auth_router.post("/password-reset/confirm")
async def confirm_password_reset(data: PasswordResetConfirm, session: AsyncSession = Depends(get_session)):
    user = await user_service.get_user_by_email(data.email, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Verify OTP
    if user.otp_code != data.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    if user.otp_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")
    # Update password
    user.password_hash = generate_passwd_hash(data.new_password)
    user.otp_code = None
    user.otp_expiry = None
    await session.commit()
    await session.refresh(user)
    return {"message": "Password reset successful"}