from datetime import timedelta

from django.db.models import Case, DateTimeField, F, IntegerField, Q, Value, When
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import AdminGroupModelPermissionsOrReadOnly, is_portal_admin
from rest_framework.viewsets import ModelViewSet

from core.models import Message
from core.serializers import MessageListRetrieveSerializer, MessageSerializer


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.select_related('pastoral', 'category', 'autor', 'image').all()
    permission_classes = [AdminGroupModelPermissionsOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pastoral', 'category', 'is_notice']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('admin_all') == '1':
            if not is_portal_admin(self.request.user) or not self.request.user.has_perm('core.view_message'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Sem permissão para consultar todas as publicações.')
            return queryset.order_by('-created_at', '-pk')
        if self.action not in {'list', 'retrieve'}:
            return queryset
        if self.request.query_params.get('is_notice') == 'true':
            return queryset.order_by('-created_at', '-pk')

        now = timezone.now()
        return (
            queryset.filter(Q(event_date__isnull=True) | Q(event_date__gte=now - timedelta(days=7)))
            .annotate(
                event_date_group=Case(
                    When(event_date__isnull=True, then=Value(2)),
                    When(event_date__lt=now, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                upcoming_event_date=Case(
                    When(event_date__gte=now, then=F('event_date')),
                    output_field=DateTimeField(),
                ),
                past_event_date=Case(
                    When(event_date__lt=now, then=F('event_date')),
                    output_field=DateTimeField(),
                ),
            )
            .order_by('event_date_group', 'upcoming_event_date', '-past_event_date', '-created_at')
        )

    def paginate_queryset(self, queryset):
        if self.request.query_params.get('admin_all') == '1':
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return MessageListRetrieveSerializer
        return MessageSerializer
