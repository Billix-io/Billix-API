from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from schemas.roles_schemas import RoleCreate, RoleUpdate, RoleResponse
from models.enums import RoleEnum
from database import get_session
from DAL_files.roles_dal import RoleDAL
from dependencies import RoleChecker, get_current_user

# Only super_admin can manage roles
super_admin_checker = Depends(RoleChecker([RoleEnum.super_admin]))

roles_router = APIRouter()
role_service = RoleDAL()

"""
Endpoints for managing user roles: create, retrieve, update, list, and delete roles.
Only super_admin can manage roles.
"""

@roles_router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate, 
    session: AsyncSession = Depends(get_session), 
    
):
    """
    Create a new user role. Fails if a role with the same name exists.
    """
    # Check if role with the same name already exists
    existing_role = await role_service.get_role_by_name(role.name, session)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists."
        )
    created_role = await role_service.create_role(role, session)
    return created_role

@roles_router.get("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK, dependencies=[super_admin_checker])
async def get_role_by_id(
    role_id: str, 
    session: AsyncSession = Depends(get_session)
):
    """
    Retrieve a user role by its ID. Only accessible by super_admin.
    """
    role = await role_service.get_role_by_id(role_id, session)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found."
        )
    return role

@roles_router.get("/", response_model=list[RoleResponse], status_code=status.HTTP_200_OK, dependencies=[super_admin_checker])
async def get_all_roles(
    session: AsyncSession = Depends(get_session)
):
    """
    List all user roles. Only accessible by super_admin.
    """
    roles = await role_service.get_all_roles(session)
    return roles

@roles_router.put("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK, dependencies=[super_admin_checker])
async def update_role(
    role_id: str, 
    role_update: RoleUpdate, 
    session: AsyncSession = Depends(get_session)
):
    """
    Update a user role by its ID. Only accessible by super_admin.
    """
    updated_role = await role_service.update_role(role_id, role_update, session)
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found."
        )
    return updated_role

@roles_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[super_admin_checker])
async def delete_role(
    role_id: str, 
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a user role by its ID. Only accessible by super_admin.
    """
    success = await role_service.delete_role(role_id, session)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found."
        )
    return