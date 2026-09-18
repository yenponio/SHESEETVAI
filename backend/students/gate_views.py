from rest_framework.decorators import api_view
from rest_framework.response import Response
from .gate import cycle_status
from .models import GateCycle


@api_view(["GET"])
def gate_attempt_status(request, attempt_id):
    try:
        return Response(cycle_status(attempt_id))
    except GateCycle.DoesNotExist:
        return Response({"success": False, "message": "Gate attempt not found"}, status=404)
