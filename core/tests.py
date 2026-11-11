from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Category, Message, Pastoral, User
from uploader.models import Image


class MessageListOrderingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Evento')
        self.pastoral = Pastoral.objects.create(name='Pastoral')
        self.user = User.objects.create(email='test@example.com')
        self.image = Image.objects.create(file='images/test.jpg')

    def create_message(self, title, event_date):
        return Message.objects.create(
            title=title,
            text=title,
            autor=self.user,
            image=self.image,
            event_date=event_date,
            pastoral=self.pastoral,
            category=self.category,
        )

    def test_orders_upcoming_then_recent_past_then_undated(self):
        now = timezone.now()
        upcoming_later = self.create_message('upcoming later', now + timedelta(days=2))
        upcoming_soon = self.create_message('upcoming soon', now + timedelta(days=1))
        past_earlier = self.create_message('past earlier', now - timedelta(days=2))
        past_recent = self.create_message('past recent', now - timedelta(days=1))
        undated = self.create_message('undated', None)

        response = self.client.get(reverse('recados-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['id'] for item in response.data],
            [
                str(upcoming_soon.id),
                str(upcoming_later.id),
                str(past_recent.id),
                str(past_earlier.id),
                str(undated.id),
            ],
        )

    def test_excludes_events_more_than_seven_days_old_from_api(self):
        expired = self.create_message('expired', timezone.now() - timedelta(days=7, minutes=1))
        recent = self.create_message('recent', timezone.now() - timedelta(days=6))

        response = self.client.get(reverse('recados-list'))
        retrieve_response = self.client.get(reverse('recados-detail', args=[expired.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [str(recent.id)])
        self.assertEqual(retrieve_response.status_code, 404)
