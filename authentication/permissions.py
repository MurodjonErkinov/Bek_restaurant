from rest_framework.permissions import BasePermission


EMPLOYEE_ROLES = {'admin', 'kassir', 'afitsant', 'oshpaz'}


def has_role(user, roles):
    return (
        user
        and user.is_authenticated
        and user.is_active
        and (user.is_superuser or user.role in roles)
    )


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, EMPLOYEE_ROLES)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, {'admin'})


class IsAdminOrCashier(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, {'admin', 'kassir'})


class IsAdminOrCashierOrWaiter(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, {'admin', 'kassir', 'afitsant'})


class IsAdminOrChef(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, {'admin', 'oshpaz'})
