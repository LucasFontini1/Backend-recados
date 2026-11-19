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


class AdministrationWorkflowTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group, Permission
        self.client = APIClient()
        self.viewer = User.objects.create_user(
            email='questioner@example.com', password='safePassword123', name='Perguntador'
        )
        self.other = User.objects.create_user(
            email='another@example.com', password='safePassword123', name='Outro'
        )
        self.admin_user = User.objects.create_user(
            email='director@example.com', password='safePassword123', name='Diretor'
        )
        self.admin_user.groups.set([Group.objects.get(name='admin')])
        self.admin_user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label='core',
                codename__in=[
                    'view_question', 'change_question', 'view_message',
                    'change_message', 'delete_message', 'view_user', 'delete_user',
                ],
            )
        )
        self.pastoral = Pastoral.objects.create(name='Pastoral teste')
        self.category = Category.objects.create(name='Categoria teste')

    def test_answer_is_visible_only_to_its_author_and_administrators(self):
        from core.models import Question
        question = Question.objects.create(
            subject='Dúvida', text='Quando será?', author=self.viewer
        )
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get('/api/perguntas/').status_code, 403)
        own = self.client.get('/api/perguntas/minhas/')
        self.assertEqual(own.status_code, 200)
        self.assertEqual(len(own.data), 1)
        self.assertEqual(own.data[0]['answer'], '')
        self.assertEqual(self.client.post(f'/api/perguntas/{question.id}/responder/', {'answer': 'Olá'}).status_code, 403)

        self.client.force_authenticate(self.admin_user)
        reply = self.client.post(f'/api/perguntas/{question.id}/responder/', {
            'answer': 'A reunião será no domingo.'
        })
        self.assertEqual(reply.status_code, 200)
        self.assertIsNotNone(reply.data['answered_at'])
        self.assertEqual(reply.data['answer'], 'A reunião será no domingo.')

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/perguntas/minhas/').data, [])
        self.client.force_authenticate(self.viewer)
        self.assertEqual(
            self.client.get('/api/perguntas/minhas/').data[0]['answer'],
            'A reunião será no domingo.',
        )

    def test_notice_listing_orders_newest_first(self):
        first = Message.objects.create(
            title='Antigo', text='Texto', autor=self.admin_user,
            pastoral=self.pastoral, category=self.category, is_notice=True,
        )
        second = Message.objects.create(
            title='Novo', text='Texto', autor=self.admin_user,
            pastoral=self.pastoral, category=self.category, is_notice=True,
        )
        response = self.client.get('/api/recados/?is_notice=true')
        self.assertEqual(response.status_code, 200)
        data = response.data['results'] if isinstance(response.data, dict) else response.data
        self.assertEqual([x['id'] for x in data][:2], [str(second.id), str(first.id)])

    def test_admin_can_access_archived_messages_and_full_history(self):
        expired = Message.objects.create(
            title='Evento antigo', text='Texto', autor=self.admin_user,
            pastoral=self.pastoral, category=self.category, is_notice=False,
            event_date=timezone.now() - timedelta(days=30),
        )
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get('/api/recados/?admin_all=1').status_code, 403)
        self.client.force_authenticate(self.admin_user)
        response = self.client.get('/api/recados/?admin_all=1')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertIn(str(expired.id), [x['id'] for x in response.data])

    def test_administrator_can_delete_other_users_but_not_self(self):
        self.client.force_authenticate(self.admin_user)
        self.assertEqual(self.client.delete(f'/api/usuarios/{self.other.pk}/').status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.other.pk).exists())
        self.assertEqual(self.client.delete(f'/api/usuarios/{self.admin_user.pk}/').status_code, 400)

    def test_edit_message_does_not_change_original_author(self):
        notice = Message.objects.create(
            title='Aviso inicial', text='Texto', autor=self.viewer,
            pastoral=self.pastoral, category=self.category, is_notice=True,
        )
        self.client.force_authenticate(self.admin_user)
        response = self.client.put(f'/api/recados/{notice.pk}/', {
            'title': 'Aviso revisado', 'text': 'Texto atualizado',
            'pastoral': self.pastoral.pk, 'category': self.category.pk, 'is_notice': True,
        })
        self.assertEqual(response.status_code, 200)
        notice.refresh_from_db()
        self.assertEqual(notice.autor_id, self.viewer.pk)
        self.assertEqual(notice.title, 'Aviso revisado')


class ProtectedAdminRolesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_group = Group.objects.get(name='admin')
        self.superadmin_group = Group.objects.get(name='superadmin')

        self.admin = User.objects.create_user(
            email='manager@example.com', password='strong-password-123',
        )
        self.admin.groups.set([self.admin_group])
        self.admin.user_permissions.add(*Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(User),
            codename__in=['view_user', 'change_user', 'delete_user'],
        ))
        self.another_admin = User.objects.create_user(
            email='another-admin@example.com', password='strong-password-123',
        )
        self.another_admin.groups.set([self.admin_group])
        self.superadmin = User.objects.create_user(
            email='super-admin@example.com', password='strong-password-123',
        )
        self.superadmin.groups.set([self.superadmin_group])
        self.viewer = User.objects.create_user(
            email='regular-viewer@example.com', password='strong-password-123',
        )

    def test_superadmin_group_is_created_by_migration(self):
        self.assertTrue(Group.objects.filter(name='superadmin').exists())

    def test_admin_can_promote_viewer(self):
        self.client.force_authenticate(self.admin)
        result = self.client.post(
            f'/api/usuarios/{self.viewer.pk}/grupo/', {'group': 'admin'},
        )
        self.assertEqual(result.status_code, 200)
        self.assertTrue(self.viewer.groups.filter(name='admin').exists())

    def test_admin_cannot_demote_or_delete_another_admin(self):
        self.client.force_authenticate(self.admin)
        url = f'/api/usuarios/{self.another_admin.pk}/'
        self.assertEqual(
            self.client.post(url + 'grupo/', {'group': 'viewer'}).status_code, 400,
        )
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.assertTrue(self.another_admin.groups.filter(name='admin').exists())
        self.assertTrue(User.objects.filter(pk=self.another_admin.pk).exists())

    def test_superadmin_cannot_be_changed_or_deleted_through_portal(self):
        self.client.force_authenticate(self.admin)
        url = f'/api/usuarios/{self.superadmin.pk}/'
        self.assertEqual(
            self.client.post(url + 'grupo/', {'group': 'viewer'}).status_code, 400,
        )
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.assertTrue(self.superadmin.groups.filter(name='superadmin').exists())

    def test_portal_cannot_assign_superadmin_group(self):
        self.client.force_authenticate(self.admin)
        result = self.client.post(
            f'/api/usuarios/{self.viewer.pk}/grupo/', {'group': 'superadmin'},
        )
        self.assertEqual(result.status_code, 400)
        self.assertFalse(self.viewer.groups.filter(name='superadmin').exists())

    def test_superadmin_has_portal_access_but_not_automatic_django_permissions(self):
        from core.permissions import is_portal_admin
        self.assertTrue(is_portal_admin(self.superadmin))
        self.assertFalse(self.superadmin.has_perm('core.delete_user'))

    def test_superadmin_can_demote_and_delete_admin(self):
        self.superadmin.user_permissions.add(*Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(User),
            codename__in=['view_user', 'change_user', 'delete_user'],
        ))
        self.client.force_authenticate(self.superadmin)
        response = self.client.post(
            f'/api/usuarios/{self.another_admin.pk}/grupo/',
            {'group': 'viewer'},
        )
        self.assertEqual(response.status_code, 200)
        self.another_admin.refresh_from_db()
        self.assertTrue(self.another_admin.groups.filter(name='viewer').exists())
        self.another_admin.groups.set([self.admin_group])
        response = self.client.delete(f'/api/usuarios/{self.another_admin.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.another_admin.pk).exists())

    def test_superadmin_cannot_change_or_delete_another_superadmin(self):
        second = User.objects.create_user(
            email='second-superadmin@example.com', password='strong-password-123',
        )
        second.groups.set([self.superadmin_group])
        self.superadmin.user_permissions.add(*Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(User),
            codename__in=['view_user', 'change_user', 'delete_user'],
        ))
        self.client.force_authenticate(self.superadmin)
        self.assertEqual(
            self.client.post(
                f'/api/usuarios/{second.pk}/grupo/', {'group': 'viewer'},
            ).status_code,
            400,
        )
        self.assertEqual(self.client.delete(f'/api/usuarios/{second.pk}/').status_code, 400)


class PublicHomePerformanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.pastoral = Pastoral.objects.create(name='Comunidade')
        self.category = Category.objects.create(name='Avisos')
        self.user = User.objects.create_user(email='homeperf@example.com', password='safePassword123')

    def test_home_combines_four_public_resources_without_authentication(self):
        from core.models import Message
        event = Message.objects.create(
            title='Evento futuro', text='Detalhes', autor=self.user, pastoral=self.pastoral,
            category=self.category, event_date=timezone.now() + timedelta(days=1), is_notice=False,
        )
        notice = Message.objects.create(
            title='Aviso novo', text='Comunicado', autor=self.user, pastoral=self.pastoral,
            category=self.category, is_notice=True,
        )
        response = self.client.get('/api/home/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['messages'][0]['id'], str(event.id))
        self.assertEqual(response.data['notices'][0]['id'], str(notice.id))
        self.assertEqual(response.data['pastorals'][0]['name'], self.pastoral.name)
        self.assertEqual(response.data['categories'][0]['name'], self.category.name)

    def test_home_excludes_old_events_and_limits_public_lists(self):
        from core.models import Message
        Message.objects.create(
            title='Evento vencido', text='Expirado', autor=self.user, pastoral=self.pastoral,
            category=self.category, event_date=timezone.now() - timedelta(days=30),
            is_notice=False,
        )
        for number in range(12):
            Message.objects.create(
                title=f'Aviso {number}', text='Comunicado', autor=self.user,
                pastoral=self.pastoral, category=self.category, is_notice=True,
            )
        response = self.client.get('/api/home/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['messages'], [])
        self.assertEqual(len(response.data['notices']), 10)


class NoticeImageRulesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='image-admin@example.com', password='strongPassword123',
        )
        self.admin.groups.set([Group.objects.get(name='admin')])
        self.admin.user_permissions.add(*Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Message),
            codename__in=['add_message', 'change_message'],
        ))
        self.pastoral = Pastoral.objects.create(name='Pastoral de imagem')
        self.category = Category.objects.create(name='Categoria de imagem')
        self.image = Image.objects.create(file='images/test.jpg')
        self.client.force_authenticate(self.admin)

    def payload(self, **overrides):
        data = {
            'title': 'Recado de teste',
            'text': 'Texto',
            'pastoral': self.pastoral.pk,
            'category': self.category.pk,
            'is_notice': False,
        }
        data.update(overrides)
        return data

    def test_event_can_have_image(self):
        response = self.client.post('/api/recados/', self.payload(
            attachment_key=str(self.image.attachment_key),
        ))
        self.assertEqual(response.status_code, 201)
        message = Message.objects.get(pk=response.data['id'])
        self.assertEqual(message.image_id, self.image.pk)

    def test_notice_cannot_have_image(self):
        response = self.client.post('/api/recados/', self.payload(
            is_notice=True,
            attachment_key=str(self.image.attachment_key),
        ))
        self.assertEqual(response.status_code, 400)
        self.assertIn('attachment_key', response.data)

    def test_update_can_remove_image_when_converting_to_notice(self):
        message = Message.objects.create(
            title='Evento com imagem', text='Texto', autor=self.admin,
            pastoral=self.pastoral, category=self.category,
            image=self.image, is_notice=False,
        )
        response = self.client.put(f'/api/recados/{message.pk}/', self.payload(
            is_notice=True, attachment_key=None,
        ))
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertTrue(message.is_notice)
        self.assertIsNone(message.image)

    def test_update_rejects_notice_with_existing_image(self):
        message = Message.objects.create(
            title='Evento com imagem', text='Texto', autor=self.admin,
            pastoral=self.pastoral, category=self.category,
            image=self.image, is_notice=False,
        )
        response = self.client.put(f'/api/recados/{message.pk}/', self.payload(
            is_notice=True,
        ))
        self.assertEqual(response.status_code, 400)
