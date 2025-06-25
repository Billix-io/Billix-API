from enum import Enum

class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"
    super_admin = "super_admin" 