from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied

from core.models import User
from core.serializers import UserRegistrationSerializer, UserSerializer
from core.serializers.user import UserGroupUpdateSerializer
from core.permissions import is_portal_admin


def can_manage_target(actor, target):
    # Superadmins podem gerenciar admins; admins não podem gerenciar outros admins.
    # Contas superadmin e superusuários Django permanecem protegidas no portal.
    if target.is_superuser or target.pk == actor.pk:
        return False
    if target.groups.filter(name='superadmin').exists():
        return False
    if target.groups.filter(name='admin').exists():
        return actor.is_superuser or actor.groups.filter(name='superadmin').exists()
    return True


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        if self.action == 'me':
            return User.objects.filter(pk=self.request.user.pk)
        if not is_portal_admin(self.request.user) or not self.request.user.has_perm('core.view_user'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Sem permissão para listar usuários.')
        return super().get_queryset()

    def paginate_queryset(self, queryset):
        return None

    def destroy(self, request, *args, **kwargs):
        if not is_portal_admin(request.user) or not request.user.has_perm('core.delete_user'):
            raise PermissionDenied('Sem permissão para excluir usuários.')
        user = self.get_object()
        if not can_manage_target(request.user, user):
            return Response({'detail': 'Não é permitido excluir este usuário.'}, status=400)
        user.delete()
        return Response(status=204)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    @action(detail=True, methods=['post'], url_path='grupo')
    def set_group(self, request, pk=None):
        if not is_portal_admin(request.user) or not request.user.has_perm('core.change_user'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Sem permissão para alterar grupos.')
        target = self.get_object()
        if not can_manage_target(request.user, target):
            return Response({'detail': 'Não é permitido alterar este usuário.'}, status=400)
        serializer = UserGroupUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(target, serializer.validated_data)
        return Response(UserSerializer(target).data)


    @extend_schema(
        summary="Dados do usuário autenticado",
        description="Retorna os dados do usuário autenticado.",
        responses={200: UserSerializer, 401: None},
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """ Retorna os dados do usuário autenticado."""
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Registro de novo usuário",
    description="Cria um novo usuário no sistema. Não requer autenticação.",
    request=UserRegistrationSerializer,
    responses={201: UserRegistrationSerializer, 400: None},
)
class UserRegistrationView(CreateAPIView):
    """Endpoint para registro de novos usuários."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
