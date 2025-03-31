from rest_framework.permissions import BasePermission
from judge.models.problem import Problem

class CanEditProblem(BasePermission):
    def has_object_permission(self, request, view, obj:Problem):
        return obj.is_editable_by(request.user)
    
class CanCreateProblem(BasePermission):
    def has_permission(self, request, view):

        if request.user.has_perm("judge.create_problem"):
            return True
        return False