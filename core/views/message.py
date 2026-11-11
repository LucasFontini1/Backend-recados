from datetime import timedelta

from django.db.models import Case, DateTimeField, F, IntegerField, Q, Value, When
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet
from django.utils import timezone

from core.models import Message
from core.serializers import MessageListRetrieveSerializer, MessageSerializer


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all()
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action not in {'list', 'retrieve'}:
            return queryset

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

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return MessageListRetrieveSerializer
        return MessageSerializer
