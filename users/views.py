

# Create your views here.
from django.shortcuts import render


def register_user(request):
    from users.choices import PROVINCIAS_CHOICES
    context = {'provinces': PROVINCIAS_CHOICES}
    return render(request, 'users/register_user.html', context)
