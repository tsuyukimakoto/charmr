from django.contrib.auth.forms import AuthenticationForm


def event_context(request):
    """
    """
    return {
        'login_form': AuthenticationForm(),
    }
