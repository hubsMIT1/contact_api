from .models import SpamReport
from rest_framework import permissions
from django_ratelimit.decorators import ratelimit
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from decouple import config

def calculate_spam_likelihood(phone_number):
    total_users = SpamReport.objects.values('reporter').distinct().count()
    spam_reports = SpamReport.objects.filter(phone_number=phone_number).count()
    
    if total_users == 0:
        return 0
    
    return min(spam_reports / total_users, 1.0)

class IsAdminOrSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff
    


def custom_ratelimit(rate, method='GET', key='ip'):
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key=key, rate=rate, method=method)
        def _wrapped_view(request, *args, **kwargs):
            if not config('DEBUG', default=False, cast=bool):
                was_limited = getattr(request, 'limited', False)
                if was_limited:
                    return Response({"detail": "Request was throttled."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator