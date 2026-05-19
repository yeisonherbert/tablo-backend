from typing import Any

from strawberry.permission import BasePermission
from strawberry.types import Info


class IsAuthenticated(BasePermission):
    message = "No autenticado: se requiere un JWT válido en Authorization."

    async def has_permission(
        self, source: Any, info: Info, **kwargs: Any
    ) -> bool:
        return getattr(info.context, "user", None) is not None
