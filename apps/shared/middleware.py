from django.db import connection

class CloseDBConnectionMiddleware:
    """Ensures database connections are closed after every request to avoid Supabase client limit."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        connection.close()
        return response
