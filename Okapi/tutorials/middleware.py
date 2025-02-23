from django.shortcuts import redirect
from django.urls import reverse

class UserRoleRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before the view is called
        if request.user.is_authenticated:
            # If user is authenticated, determine their correct dashboard URL
            dashboard_url = None

            if request.user.groups.filter(name='admin').exists():
                dashboard_url = reverse('admin-dashboard')
            elif request.user.groups.filter(name='tutor').exists():
                dashboard_url = reverse('tutor-dashboard')
            elif request.user.groups.filter(name='student').exists():
                dashboard_url = reverse('dashboard')

            # If we found a dashboard URL and the user is not currently at that URL,
            # and isn't at the logout or login pages (to avoid loops), redirect them.
            if dashboard_url:
                # Get current path
                current_path = request.path
                # You can specify some allowed paths to avoid redirection loops
                allowed_paths = [
                    reverse('logout'),
                    reverse('login'),
                ]

                # If the user is authenticated and the current page isn't their
                # correct dashboard (and not an allowed exception), redirect them.
                # This ensures that users are always on the right dashboard if they
                # try to navigate elsewhere.
                if current_path not in allowed_paths and current_path != dashboard_url:
                    return redirect(dashboard_url)

        # Proceed with the response if no conditions met
        response = self.get_response(request)
        return response
