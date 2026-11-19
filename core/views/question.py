from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from core.models import Question
from core.permissions import is_portal_admin
from core.serializers.question import QuestionSerializer

class QuestionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Question.objects.select_related('author').all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list':
            if not is_portal_admin(self.request.user) or not self.request.user.has_perm('core.view_question'):
                raise PermissionDenied('Sem permissão para ver perguntas da diretoria.')
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
