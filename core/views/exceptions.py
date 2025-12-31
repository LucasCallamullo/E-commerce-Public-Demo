

from django_ratelimit.exceptions import Ratelimited
from django.shortcuts import render

def rate_limit_view(request, exception=None):
    if isinstance(exception, Ratelimited):
        return render(request, 'errors/ratelimit.html', status=429)
    return render(request, 'errors/403.html', status=403)