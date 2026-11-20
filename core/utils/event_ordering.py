"""Regras compartilhadas de visibilidade e ordenação dos eventos públicos."""

from datetime import datetime, time, timedelta

from django.db.models import Case, DateTimeField, F, IntegerField, Q, Value, When
from django.utils import timezone


def visible_events(queryset, now=None):
    """
    Mostra eventos futuros, do dia atual e do dia anterior.

    Sem próximos eventos, o evento mais recente fica no início até o fim
    do dia seguinte à data programada. Eventos sem data vêm por último.
    """
    now = now or timezone.now()
    local_today = timezone.localtime(now).date()
    yesterday = local_today - timedelta(days=1)
    cutoff = timezone.make_aware(
        datetime.combine(yesterday, time.min),
        timezone.get_current_timezone(),
    )

    return (
        queryset.filter(
            Q(event_date__isnull=True) | Q(event_date__gte=cutoff)
        )
        .annotate(
            event_date_group=Case(
                When(event_date__gte=now, then=Value(0)),
                When(event_date__isnull=True, then=Value(3)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            upcoming_event_date=Case(
                When(event_date__gte=now, then=F("event_date")),
                output_field=DateTimeField(),
            ),
            past_event_date=Case(
                When(event_date__lt=now, then=F("event_date")),
                output_field=DateTimeField(),
            ),
        )
        .order_by(
            "event_date_group",
            "upcoming_event_date",
            "-past_event_date",
            "-created_at",
        )
    )
