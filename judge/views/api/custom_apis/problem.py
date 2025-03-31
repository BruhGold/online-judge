from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticated
from ..serializers.problem import ProblemSerializer
from ..permissions.problem import CanEditProblem, CanCreateProblem

class APIProblemCreateView(APIView):
    permission_classes = [IsAuthenticated, CanEditProblem]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        serializer = ProblemSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            try:
                problem = serializer.save()
                return Response(ProblemSerializer(problem).data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response(
                    {"error": "Database constraint error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APIProblemEditView(APIView):
    def get(self,request):
        pass

    def delete(self,request):
        pass