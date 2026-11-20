from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from core.models import Message
from core.permissions import AdminGroupModelPermissionsOrReadOnly, is_portal_admin
from core.serializers import MessageListRetrieveSerializer, MessageSerializer
from core.utils.event_ordering import visible_events


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.select_related(
        "pastoral", "category", "autor", "image"
    ).all()
    permission_classes = [AdminGroupModelPermissionsOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["pastoral", "category", "is_notice"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.query_params.get("admin_all") == "1":
            user = self.request.user
            if not is_portal_admin(user) or not user.has_perm("core.view_message"):
                raise PermissionDenied(
                    "Sem permissão para consultar todas as publicações."
                )
            return queryset.order_by("-created_at", "-pk")

        if self.action not in {"list", "retrieve"}:
            return queryset

        if self.request.query_params.get("is_notice") == "true":
            return queryset.order_by("-created_at", "-pk")

        return visible_events(queryset)

    def paginate_queryset(self, queryset):
        if self.request.query_params.get("admin_all") == "1":
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return MessageListRetrieveSerializer
        return MessageSerializer
