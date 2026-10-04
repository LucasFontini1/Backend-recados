from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from core.models import Category
from core.serializers import CategorySerializer


class CategoryViewSet(ModelViewSet):

    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'delete']
