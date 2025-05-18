from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.urls import reverse
from judge.models.problem import Problem
from judge.models.problem_data import ProblemData, ProblemTestCase
from ..permissions.problem import CanEditProblem
from ..serializers.problem_data import ProblemFullDataSerializer
from judge.views.problem_data import ProblemManagerMixin

class APIProblemDataView(APIView, ProblemManagerMixin):
    permission_classes = [IsAuthenticated,CanEditProblem]
    parser_classes = [MultiPartParser]

    def get(self, request, *args, **kwargs):
        problem = self.get_object()
        try:
            problem_data = problem.data_files
        except ProblemData.DoesNotExist:
            return Response({"detail": "ProblemData not found."}, status=status.HTTP_404_NOT_FOUND)

        cases = ProblemTestCase.objects.filter(dataset_id=problem.id)
        serializer = ProblemFullDataSerializer({
            "problem_data": problem_data,
            "test_cases": cases
        })

        zipfile_exists = bool(problem_data.zipfile)
        zipfile_url = None
        if problem_data.zipfile:
            zipfile_url = request.build_absolute_uri(problem_data.zipfile.url)

        return Response({
            "zipfile_exists": zipfile_exists,
            "zipfile_download_url": zipfile_url,
            "data": serializer.data
        })

    def post(self, request, *args, **kwargs):
        problem = self.get_object()
        self.check_object_permissions(request, problem)

        zipfile = request.FILES.get('problem_data.zipfile')
        if request.data.get('clear') == "True":
            zipfile = None

        # Problem Data handling
        problem_data = {
            'zipfile': zipfile,
            'generator': request.FILES.get('problem_data.generator'),
            'output_prefix': request.data.get('problem_data.output_prefix'),
            'output_limit': request.data.get('problem_data.output_limit'),
            'feedback': request.data.get('problem_data.feedback'),
            'checker': request.data.get('problem_data.checker'),
            'unicode': request.data.get('problem_data.unicode'),
            'nobigmath': request.data.get('problem_data.nobigmath'),
            'checker_args': request.data.get('problem_data.checker_args')
        }



        # Test Case handling
        test_cases = []
        if zipfile is not None:
            i = 0
            while True:
                prefix = f'test_cases[{i}]'
                if f'{prefix}.input_file' not in request.data:
                    break
                test_cases.append({
                    'input_file': request.data.get(f'{prefix}.input_file'),
                    'output_file': request.data.get(f'{prefix}.output_file'),
                    'type': request.data.get(f'{prefix}.type'),
                    'order': request.data.get(f'{prefix}.order') or i + 1,
                    'points': request.data.get(f'{prefix}.points'),
                    'is_pretest': request.data.get(f'{prefix}.is_pretest'),
                })
                i += 1

        data = {
            'problem_data': problem_data,
            'test_cases': test_cases
        }

        serializer = ProblemFullDataSerializer(problem,data=data)
        if serializer.is_valid():
            response = serializer.save()
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    put = post