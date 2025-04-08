from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from judge.models.problem import Problem
from judge.models.problem_data import ProblemData
from ..permissions.problem import CanEditProblem
from ..serializers.problem_data import ProblemDataSerializer
from judge.utils.problem_data import ProblemDataCompiler, ProblemDataError
from judge.views.problem_data import ProblemManagerMixin

class APIProblemDataView(APIView, ProblemManagerMixin):
    permission_classes = [IsAuthenticated,CanEditProblem]
    parser_classes = [MultiPartParser]

    def get(self, request, *args, **kwargs):
        problem_obj = self.get_object()
        try:
            problem_data = problem_obj.data_files
        except ProblemData.DoesNotExist:
            return Response({"detail": "ProblemData not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProblemDataSerializer(problem_data)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        problem_obj = self.get_object()
        self.check_object_permissions(request, problem_obj)
        return super().put(request, problem_obj, *args, **kwargs)