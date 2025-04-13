from rest_framework.permissions import BasePermission, SAFE_METHODS
from judge.models.problem import Problem

class CanEditProblem(BasePermission):
    def has_object_permission(self, request, view, obj:Problem):
        if request.method == "PUT" or request.method == "DELETE":
            return obj.is_editable_by(request.user)
        return True
    
class CanCreateProblem(BasePermission):
    def has_permission(self, request, view): 
        if request.method == "POST":
            return request.user.has_perm("judge.add_problem")
        return True
    
class CanDeleteProblem(BaseException):
    def has_permission(self, request, view):    
        if request.method == "DELETE":
            return request.user.has_perm("judge.delete_problem")
        return True
    
    def has_object_permission(self, request, view, obj:Problem):
        return True