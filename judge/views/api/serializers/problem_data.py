from rest_framework import serializers
from judge.models.problem_data import ProblemData
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
