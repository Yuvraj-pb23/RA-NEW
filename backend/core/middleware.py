from django.utils.deprecation import MiddlewareMixin
from accounts.models import SystemRole

class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware to naturally attach the appropriate organization to the request
    so it's easily accessible in views and templates without repetitive lookups.
    """
    def process_request(self, request):
        request.organization = None
        
        if request.user.is_authenticated:
            # If the user has a specific organization, attach it
            if getattr(request.user, 'organization', None):
                request.organization = request.user.organization
