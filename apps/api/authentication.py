from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication scheme used by DRF that exempts from CSRF checks.
    Use only for development!
    """
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening
