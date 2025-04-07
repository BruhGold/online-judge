from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from ..serializers.problem import ProblemSerializer
from judge.models.problem_data import ProblemData
from ..permissions.problem import *
import judge.views.api.api_v2 as api_v2

class APIProblemListView(APIView, api_v2.APIProblemList):
    permission_classes = [IsAuthenticatedOrReadOnly, CanCreateProblem]

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request):
        data = request.data.copy()

        # forcing request sender as authour you can adjust this if you want to
        user_id = request.user.pk
        if 'authors' not in data or user_id not in data.get('authors', []):
            data.setdefault('authors', []).append(user_id)

        serializer = ProblemSerializer(data=data, context={'user': request.user})

        if serializer.is_valid():
            try:
                problem = serializer.save()
                ProblemData.objects.create(problem=problem)
                return Response(ProblemSerializer(problem).data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response(
                    {"error": "Database constraint error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class APIProblemDetailView(APIView, api_v2.APIProblemDetail):
    permission_classes = [IsAuthenticatedOrReadOnly, CanDeleteProblem, CanEditProblem]
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def put(self,request, *args, **kwargs):
        problem = self.get_object()

        self.check_object_permissions(request, problem)

        serializer = ProblemSerializer(problem, data=request.data, partial=True, context={'user': request.user})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request, *args, **kwargs):
        problem = self.get_object()
        self.check_object_permissions(request, problem)
        problem.delete()
        return Response({"detail": "Problem deleted successfully."},status=status.HTTP_204_NO_CONTENT)