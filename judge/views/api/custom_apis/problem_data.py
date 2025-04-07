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

class APIProblemDataView(APIView):
    permission_classes = [IsAuthenticated,CanEditProblem]
    parser_classes = [MultiPartParser]

    def get_object(self, problem_code):
        problem = get_object_or_404(Problem, code=problem_code)
        self.check_object_permissions(self.request, problem)
        return problem

    def get(self, request, problem, *args, **kwargs):
        problem_obj = self.get_object(problem)
        try:
            problem_data = problem_obj.data_files
        except ProblemData.DoesNotExist:
            return Response({"detail": "ProblemData not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProblemDataSerializer(problem_data)
        return Response(serializer.data)

    def put(self, request, problem, *args, **kwargs):
        problem_obj = self.get_object(problem)
        self.check_object_permissions(request, problem_obj)

        try:
            problem_data = problem_obj.data_files
        except ProblemData.DoesNotExist:
            return Response({"detail": "ProblemData not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProblemDataSerializer(problem_data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)