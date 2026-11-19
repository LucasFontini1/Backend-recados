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
            [item['id'] for item in (response.data['results'] if isinstance(response.data, dict) else response.data)],
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
        self.assertEqual([item['id'] for item in (response.data['results'] if isinstance(response.data, dict) else response.data)], [str(recent.id)])
        self.assertEqual(retrieve_response.status_code, 404)


from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class PortalPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.viewer = User.objects.create_user(
            email='viewer@exemplo.com', password='senhaSegura123', name='Viewer'
        )
        self.admin_user = User.objects.create_user(
            email='admin@exemplo.com', password='senhaSegura123', name='Administrador'
        )
        self.admin_group = Group.objects.get(name='admin')
        self.admin_user.groups.set([self.admin_group])

    def grant(self, user, model, codename):
        permission = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(model),
            codename=codename,
        )
        user.user_permissions.add(permission)
        for attr in ('_perm_cache', '_user_perm_cache', '_group_perm_cache'):
            if hasattr(user, attr):
                delattr(user, attr)

    def test_register_assigns_viewer_by_default(self):
        response = self.client.post('/api/registro/', {
            'email': 'novo@exemplo.com', 'name': 'Novo', 'password': 'senhaSegura123'
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.get(email='novo@exemplo.com').groups.filter(name='viewer').exists())

    def test_viewer_cannot_create_pastorals_or_categories(self):
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.post('/api/pastorais/', {'name': 'Nova'}).status_code, 403)
        self.assertEqual(self.client.post('/api/categorias/', {'name': 'Nova'}).status_code, 403)

    def test_admin_needs_django_add_permission(self):
        self.client.force_authenticate(self.admin_user)
        self.assertEqual(self.client.post('/api/categorias/', {'name': 'Teste'}).status_code, 403)
        self.grant(self.admin_user, Category, 'add_category')
        self.assertEqual(self.client.post('/api/categorias/', {'name': 'Teste'}).status_code, 201)

    def test_viewer_can_send_question_but_not_read_inbox(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post('/api/perguntas/', {
            'subject': 'Horários', 'text': 'Quando é a próxima reunião?'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get('/api/perguntas/').status_code, 403)

    def test_admin_needs_permission_to_read_questions(self):
        self.client.force_authenticate(self.admin_user)
        self.assertEqual(self.client.get('/api/perguntas/').status_code, 403)
        from core.models import Question
        self.grant(self.admin_user, Question, 'view_question')
        self.assertEqual(self.client.get('/api/perguntas/').status_code, 200)

    def test_group_change_requires_permission_and_rejects_self_change(self):
        self.client.force_authenticate(self.admin_user)
        url = f'/api/usuarios/{self.viewer.pk}/grupo/'
        self.assertEqual(self.client.post(url, {'group': 'admin'}).status_code, 403)
        self.grant(self.admin_user, User, 'view_user')
        self.grant(self.admin_user, User, 'change_user')
        self.assertEqual(self.client.post(url, {'group': 'admin'}).status_code, 200)
        self.viewer.refresh_from_db()
        self.assertTrue(self.viewer.groups.filter(name='admin').exists())
        self.assertFalse(self.viewer.groups.filter(name='viewer').exists())
        own_url = f'/api/usuarios/{self.admin_user.pk}/grupo/'
        self.assertEqual(self.client.post(own_url, {'group': 'viewer'}).status_code, 400)

    def test_cannot_create_user_using_user_listing_endpoint(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post('/api/usuarios/', {
            'email': 'intruso@exemplo.com', 'password': 'senhaSegura123',
        })
        self.assertEqual(response.status_code, 405)
