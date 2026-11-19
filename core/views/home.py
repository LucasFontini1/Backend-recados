from datetime import timedelta

from django.db.models import Case, DateTimeField, F, IntegerField, Q, Value, When
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Category, Message, Pastoral
from core.serializers import CategorySerializer, MessageListRetrieveSerializer, PastoralListRetrieveSerializer


class PublicHomeView(APIView):
    """Dados necessários para exibir a home em uma única requisição HTTP."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        now = timezone.now()
        base = Message.objects.select_related('pastoral', 'category', 'autor', 'image')

        upcoming = (
            base.filter(is_notice=False)
            .filter(Q(event_date__isnull=True) | Q(event_date__gte=now - timedelta(days=7)))
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
            .order_by('event_date_group', 'upcoming_event_date', '-past_event_date', '-created_at')[:10]
        )
        notices = base.filter(is_notice=True).order_by('-created_at', '-pk')[:10]
        return Response({
            'messages': MessageListRetrieveSerializer(upcoming, many=True, context={'request': request}).data,
            'notices': MessageListRetrieveSerializer(notices, many=True, context={'request': request}).data,
            'pastorals': PastoralListRetrieveSerializer(Pastoral.objects.all().order_by('id'), many=True, context={'request': request}).data,
            'categories': CategorySerializer(Category.objects.all().order_by('id'), many=True, context={'request': request}).data,
        })
