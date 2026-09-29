from pydantic import BaseModel,ConfigDict
class RoleResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    role_id:int; role_name:str; description:str|None
class PermissionResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    permission_id:int; permission_code:str; description:str|None
class UserPermissionsResponse(BaseModel):
    user_id:int
    permissions:list[str]
class RolePermissionResponse(BaseModel):
    role_id:int; permission_id:int
