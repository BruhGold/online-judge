from rest_framework.permissions import BasePermission, SAFE_METHODS
from judge.models.problem import Problem

class CanEditProblem(BasePermission):
    def has_object_permission(self, request, view, obj:Problem):
        return obj.is_editable_by(request.user)
    
class CanCreateProblem(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif request.method == "POST":
            if request.user.has_perm("judge.add_problem"):
                return True
            return False
        return False