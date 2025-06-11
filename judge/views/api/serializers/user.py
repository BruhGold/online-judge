from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from judge.models import Submission

class DownloadDataSerializer(serializers.Serializer):
    comment_download = serializers.BooleanField(default=False, label=_('Download comments?'))
    submission_download = serializers.BooleanField(default=False, label=_('Download submissions?'))
    submission_problem_glob = serializers.CharField(
        default='*', max_length=100, label=_('Filter by problem code glob:')
    )
    submission_results = serializers.MultipleChoiceField(
        required=False,
        choices=sorted(Submission.RESULT),
        label=_('Filter by result:')
    )

    def validate(self, data):
        if not data.get('comment_download') and not data.get('submission_download'):
            raise serializers.ValidationError(
                _('Please select at least one thing to download.')
            )

        if not data.get('submission_download'):
            data['submission_problem_glob'] = '*'
            data['submission_results'] = []
        else:
            if 'submission_problem_glob' not in data or not data['submission_problem_glob']:
                data['submission_problem_glob'] = '*'
            if 'submission_results' not in data:
                data['submission_results'] = []
            else:
                data['submission_results'] = list(data.get('submission_results', []))
                
        return data
