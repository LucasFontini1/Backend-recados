from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Category, Message, Pastoral
from core.serializers import (
    CategorySerializer,
    MessageListRetrieveSerializer,
    PastoralListRetrieveSerializer,
)
from core.utils.event_ordering import visible_events


class PublicHomeView(APIView):
    """Agrupa os dados da página inicial em uma única requisição HTTP."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        base = Message.objects.select_related(
            "pastoral", "category", "autor", "image"
        )

        events = visible_events(
            base.filter(is_notice=False)
        )[:10]
        notices = base.filter(is_notice=True).order_by(
            "-created_at", "-pk"
        )[:10]
        pastorals = Pastoral.objects.all().order_by("id")
        categories = Category.objects.all().order_by("id")

        return Response(
            {
                "messages": MessageListRetrieveSerializer(
                    events,
                    many=True,
                    context={"request": request},
                ).data,
                "notices": MessageListRetrieveSerializer(
                    notices,
                    many=True,
                    context={"request": request},
                ).data,
                "pastorals": PastoralListRetrieveSerializer(
                    pastorals,
                    many=True,
                    context={"request": request},
                ).data,
                "categories": CategorySerializer(
                    categories,
                    many=True,
                    context={"request": request},
                ).data,
            }
        )
