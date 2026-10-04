from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from core.models import Pastoral
from core.serializers import PastoralListRetrieveSerializer, PastoralSerializer


class PastoralViewSet(ModelViewSet):
    queryset = Pastoral.objects.all().order_by('id')
    serializer_class = PastoralSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return PastoralListRetrieveSerializer
        return super().get_serializer_class()