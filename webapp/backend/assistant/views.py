from rest_framework.decorators import api_view
from rest_framework.response import Response
from .rag import answer_question


@api_view(["POST"])
def ask(request):
    question = (request.data.get("question") or "").strip()
    if not question:
        return Response({"error": "question is required"}, status=400)

    result = answer_question(question)
    return Response(result)
