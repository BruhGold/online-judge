from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from social_django.models import UserSocialAuth

from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.http import Http404
from rest_framework import status

import os
import json

from judge.tasks import prepare_user_data
from judge.utils.celery import task_status_by_id, task_status_url_by_id
from judge.views.user import UserDataMixin

from ..serializers.user import DownloadDataSerializer


class UserDataDownloadAPIView(APIView, UserDataMixin):
    permission_classes = [IsAuthenticated]

    @cached_property
    def _now(self):
        return timezone.now()

    @cached_property
    def can_prepare_data(self):
        return (
            self.request.user.profile.data_last_downloaded is None or
            self.request.user.profile.data_last_downloaded + settings.DMOJ_USER_DATA_DOWNLOAD_RATELIMIT < self._now or
            not os.path.exists(self.data_path)
        )

    @cached_property
    def data_cache_key(self):
        return 'celery_status_id:user_data_download_%s' % self.request.user.profile.id

    @cached_property
    def in_progress_url(self):
        status_id = cache.get(self.data_cache_key)
        status = task_status_by_id(status_id).status if status_id else None
        return (
            self.build_task_url(status_id)
            if status in ('PENDING', 'PROGRESS', 'STARTED')
            else None
        )

    def build_task_url(self, status_id):
        return task_status_url_by_id(
            status_id,
            message=_('Preparing your data...'),
            redirect=reverse('user_prepare_data')
        )

    def get(self, request, *args, **kwargs):
        if not settings.DMOJ_USER_DATA_DOWNLOAD or request.user.profile.mute:
            raise Http404()
        if os.path.exists(self.data_path):
            print("in ", self.data_path)
            return Response({
                "status": "ready",
                "download_url": request.build_absolute_uri(reverse('user_download_data'))
            })
        
        if self.in_progress_url:
            return Response({
                "status": "preparing",
                "progress_url": self.in_progress_url
            })
        
        wait_time = (
            settings.DMOJ_USER_DATA_DOWNLOAD_RATELIMIT - (self._now - request.user.profile.data_last_downloaded)
            if request.user.profile.data_last_downloaded else None
        )

        return Response({
            "status": "not_started",
            "can_prepare": self.can_prepare_data,
            "retry_after_seconds": int(wait_time.total_seconds()) if wait_time else 0
        })

    def post(self, request, *args, **kwargs):
        if not settings.DMOJ_USER_DATA_DOWNLOAD or request.user.profile.mute:
            raise Http404()

        if not self.can_prepare_data:
            raise PermissionDenied("Rate limited.")

        if self.in_progress_url is not None:
            return Response({
                "detail": "Already preparing.",
                "progress_url": self.in_progress_url
            }, status=status.HTTP_202_ACCEPTED)

        serializer = DownloadDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Start background task
        request.user.profile.data_last_downloaded = self._now
        request.user.profile.save()

        print(json.dumps(serializer.validated_data))
        task_result = prepare_user_data.delay(
            request.user.profile.id,
            json.dumps(serializer.validated_data)
        )
        cache.set(self.data_cache_key, task_result.id)

        return Response({
            "status": "started",
            "progress_url": self.build_task_url(task_result.id)
        }, status=status.HTTP_202_ACCEPTED)


class MoodleToDMOJUIDView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        provider = request.data.get("provider")
        ids = request.data.get("id", [])

        if not provider or not isinstance(ids, list):
            return Response({"error": "Invalid request format"}, status=400)

        result = {}
        for uid in ids:
            try:
                usa = UserSocialAuth.objects.get(provider=provider, uid=uid)
                result[uid] = usa.user.id
            except UserSocialAuth.DoesNotExist:
                result[uid] = "Not found"

        return Response(result)