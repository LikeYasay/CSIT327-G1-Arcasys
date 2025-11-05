from django.db import connection


class CloseDBConnectionMiddleware:
    """Only close connections if they're idle to avoid connection exhaustion"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only close if connection is idle and not in transaction
        if connection.connection and not connection.in_atomic_block:
            connection.close()

        return response