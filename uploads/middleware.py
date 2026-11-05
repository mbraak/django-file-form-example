from django.conf import settings
from django.contrib.auth import get_user_model, login

DEV_ADMIN_USERNAME = "admin"


class DebugAdminLoginMiddleware:
    """
    Development convenience: log every /admin/ visitor in as a superuser, so
    the admin works without ``createsuperuser`` or a password.

    Does nothing unless DEBUG is on. Never enable this in production.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            settings.DEBUG
            and not request.user.is_authenticated
            and request.path.startswith("/admin/")
        ):
            user, created = get_user_model().objects.get_or_create(
                username=DEV_ADMIN_USERNAME,
                defaults={"is_staff": True, "is_superuser": True},
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        return self.get_response(request)
