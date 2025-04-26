from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import status
from django.db import transaction
from judge.models import Problem, Submission, SubmissionSource, ContestSubmission
from ..serializers.submission import ProblemSubmitSerializer
from django.conf import settings
import judge.views.api.api_v2 as api_v2

class APIProblemSubmitView(APIView,api_v2.APIProblemDetail):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, *args, **kwargs):
        problem = self.get_object()
        serializer = ProblemSubmitSerializer(data=request.data, context={'request': request, 'problem': problem})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user.profile
        contest = user.current_contest

        # Submission limits
        if contest and contest.contestproblem_set.filter(problem=problem).exists():
            contest_problem = contest.contestproblem_set.get(problem=problem)
            max_subs = contest_problem.max_submissions
            if max_subs is not None:
                used = get_contest_submission_count(problem, user, contest.virtual)
                if used >= max_subs:
                    return Response({'detail': 'Submission limit exceeded.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Spam check
        if not request.user.has_perm('judge.spam_submission'):
            sub_limit = Submission.objects.filter(
                user=user, rejudged_date__isnull=True
            ).exclude(status__in=['D', 'IE', 'CE', 'AB']).count()

            if sub_limit >= settings.DMOJ_SUBMISSION_LIMIT:
                return Response({'detail': 'Too many active submissions.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        print("check 4")
        # Create and save submission
        with transaction.atomic():
            print("check 1 save")
            submission = Submission.objects.create(
                user=user,
                problem=problem,
                language=data['language'],
            )
            SubmissionSource.objects.create(submission=submission, source=data['source'])
            print("check 2 save")

            if contest and contest.contestproblem_set.filter(problem=problem).exists():
                submission.contest_object = contest.contest
                if contest.live:
                    submission.locked_after = contest.contest.locked_after
                submission.save()
                ContestSubmission.objects.create(
                    submission=submission,
                    problem=contest_problem,
                    participation=contest,
                )
            else:
                submission.save()
                print("not contest save")
            print(submission)
        judge_id = data.get('judge') or None
        submission.judge(force_judge=True, judge_id=judge_id)
        print("check 5")
        return Response({'submission_id': submission.id}, status=status.HTTP_201_CREATED)
