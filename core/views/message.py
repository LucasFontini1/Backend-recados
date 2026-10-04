from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from core.models import Message
from core.serializers import MessageListRetrieveSerializer, MessageSerializer


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all()
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return MessageListRetrieveSerializer
        return MessageSerializer
