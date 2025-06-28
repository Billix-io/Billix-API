from fastapi.security import HTTPBearer
from fastapi import Request, status, Depends, Header
from fastapi.security.http import HTTPAuthorizationCredentials
from utils import decode_token
from fastapi.exceptions import HTTPException
from database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from DAL_files.users_dal import UserDAL
from DAL_files.roles_dal import RoleDAL
from DAL_files.users_api_key_dal import UsersApiKeyDAL
from typing import List, Any, Optional
from schemas.user_schemas import UserBase
from redis_store import token_in_blocklist
from DAL_files.payment_dal import PaymentDAL
from DAL_files.user_subscription_dal import UserSubscriptionDAL
from datetime import datetime

user_service=UserDAL()
role_service=RoleDAL()

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> [HTTPAuthorizationCredentials, None]:
        creds = await super().__call__(request)    

        token= creds.credentials
        token_data=decode_token(token)

        if not self.token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="invalid or expired token" 
            )
    
        if await token_in_blocklist(token_data["jti"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="token has been blacklisted"
            )
        
        self.verify_token_data(token_data)
       
        return token_data
    
    def token_valid(self,token:str)->bool:
        token_data=decode_token(token)
        return token_data is not None 
    
    def verify_token_data(self,token_data):
         raise NotImplementedError("please Override this method in chile class")
    
class AccessTokenBearer(TokenBearer):
     def verify_token_data(self,token_data:dict)->None:
          
            if token_data and token_data["refresh"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="provide an access token"
                    )
class RefreshTokenBearer(TokenBearer):
     def verify_token_data(self,token_data:dict)->None:
          
            if token_data and not token_data["refresh"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="provide a Refresh token"
                    )

async def get_current_user(
    token_detail: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session)
):
    user_email = token_detail.get("user", {}).get("email")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token payload: missing 'user.email'."
        )

    user = await user_service.get_user_by_email(user_email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return user

async def api_key_auth(
    x_api_key: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Authenticate using API key and check token requirements
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Please provide X-API-Key header."
        )
    
    # Get API key details
    api_key_dal = UsersApiKeyDAL(session)
    api_key_record = await api_key_dal.get_api_key(x_api_key)
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )
    
    # Check if API key is expired
    # if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="API key has expired."
    #     )
    
    # Get user subscription to check tokens
    subscription_dal = UserSubscriptionDAL(session)
    has_tokens = await subscription_dal.has_minimum_tokens(api_key_record.user_id, 5000)
    
    if not has_tokens:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient tokens. You need at least 5000 tokens to access this resource."
        )
    
    # Return user_id for use in the endpoint
    return api_key_record.user_id

class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: UserBase = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> bool:
        role = await role_service.get_role_by_id(current_user.role_id, session)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role not found."
            )

        if role.name in self.allowed_roles:
            return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required role to access this resource."
        )

async def payment_required(current_user: UserBase = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    from uuid import UUID
    # Get the user's UUID (need to fetch full user object for user_id)
    user = await user_service.get_user_by_email(current_user.email, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    has_payment = await PaymentDAL.user_has_successful_payment(user.user_id, session)
    if not has_payment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API access requires a successful payment.")
    return True

async def subscription_token_required(current_user: UserBase = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    from uuid import UUID
    # Get the user's UUID (need to fetch full user object for user_id)
    user = await user_service.get_user_by_email(current_user.email, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    has_tokens = await UserSubscriptionDAL.has_minimum_tokens(user.user_id, 5000, session)
    if not has_tokens:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You need at least 5000 tokens to access this resource.")
    return True