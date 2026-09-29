from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_rbac_service,
    require_permission,
)
from app.schemas.rbac import (
    PermissionResponse,
    RolePermissionResponse,
    RoleResponse,
    UserPermissionsResponse,
)

router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"],
)


@router.get(
    "/roles",
    response_model=list[RoleResponse],
)
def get_roles(
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service=Depends(get_rbac_service),
):
    return service.get_roles()


@router.get(
    "/permissions",
    response_model=list[PermissionResponse],
)
def get_permissions(
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service=Depends(get_rbac_service),
):
    return service.get_permissions()


@router.get(
    "/users/{user_id}/permissions",
    response_model=UserPermissionsResponse,
)
def get_user_permissions(
    user_id: int,
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service=Depends(get_rbac_service),
):
    return UserPermissionsResponse(
        user_id=user_id,
        permissions=service.get_user_permissions(user_id),
    )


@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=RolePermissionResponse,
)
def assign_permission(
    role_id: int,
    permission_id: int,
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service=Depends(get_rbac_service),
):
    return service.assign_permission_to_role(
        actor_user_id=current_user.user_id,
        role_id=role_id,
        permission_id=permission_id,
    )


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
)
def revoke_permission(
    role_id: int,
    permission_id: int,
    current_user=Depends(require_permission("ROLE_MANAGE")),
    service=Depends(get_rbac_service),
):
    service.revoke_permission_from_role(
        actor_user_id=current_user.user_id,
        role_id=role_id,
        permission_id=permission_id,
    )

    return {
        "message": "Permission revoked."
    }