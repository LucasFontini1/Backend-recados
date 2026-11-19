from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import serializers

from core.models import Question
from core.permissions import is_portal_admin
from core.serializers.question import QuestionSerializer


class QuestionAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(allow_blank=False, max_length=5000, trim_whitespace=True)


class QuestionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Question.objects.select_related('author', 'answered_by').all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if self.action == 'mine':
            return super().get_queryset().filter(author=self.request.user)
        if self.action in {'list', 'answer_question'}:
            if not is_portal_admin(self.request.user) or not self.request.user.has_perm('core.view_question'):
                raise PermissionDenied('Sem permissão para ver perguntas da diretoria.')
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'], url_path='minhas')
    def mine(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='responder')
    def answer_question(self, request, pk=None):
        if not is_portal_admin(request.user) or not request.user.has_perm('core.change_question'):
            raise PermissionDenied('Sem permissão para responder perguntas.')
        question = self.get_object()
        serializer = QuestionAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question.answer = serializer.validated_data['answer']
        question.answered_by = request.user
        question.answered_at = timezone.now()
        question.save(update_fields=['answer', 'answered_by', 'answered_at'])
        return Response(self.get_serializer(question).data, status=status.HTTP_200_OK)
