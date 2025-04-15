from rest_framework import serializers
from judge.models.problem_data import ProblemData, ProblemTestCase
from zipfile import BadZipfile, ZipFile
from judge.utils.problem_data import ProblemDataCompiler, ProblemDataError
import json

class ProblemDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemData
        fields = [
            'zipfile',
            'generator',
            'output_prefix',
            'output_limit',
            'feedback',
            'checker',
            'unicode',
            'nobigmath',
            'checker_args',
        ]
        read_only_fields = ['feedback']

    def validate_checker_args(self, value):
        if value:
            try:
                parsed = json.loads(value)
                if not isinstance(parsed, dict):
                    raise serializers.ValidationError("Checker arguments must be a JSON object.")
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format in checker arguments.")
        return value

class ProblemTestCaseSerializer(serializers.ModelSerializer):
    is_pretest = serializers.BooleanField(allow_null=True, default=False)

    class Meta:
        model = ProblemTestCase
        fields = ['id', 'input_file', 'output_file', 'type', 'order', 'points', 'is_pretest']

    def validate_is_pretest(self, value):
        return value if value is not None else False

class ProblemFullDataSerializer(serializers.Serializer):
    problem_data = ProblemDataSerializer()
    test_cases = ProblemTestCaseSerializer(many=True)

    def __init__(self, *args, **kwargs):
        super(ProblemFullDataSerializer, self).__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        problem = instance

        # Save ProblemData
        problem_data_data = validated_data['problem_data']
        problem_data, created = ProblemData.objects.get_or_create(problem=problem)

        for attr, value in problem_data_data.items():
            setattr(problem_data, attr, value)
        problem_data.save()

        ProblemTestCase.objects.filter(dataset=problem).delete()
        for case_data in validated_data['test_cases']:
            ProblemTestCase.objects.create(dataset=problem, **case_data)

        valid_files = []
        if problem_data.zipfile:
            try:
                valid_files = ZipFile(problem_data.zipfile).namelist()
            except BadZipfile:
                raise serializers.ValidationError("Invalid zip file.")

        ProblemDataCompiler.generate(
            problem,
            problem_data,
            problem.cases.order_by('order'),
            valid_files,
        )

        return {"detail": "Problem data saved successfully"}