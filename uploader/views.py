from rest_framework import mixins, parsers, permissions, viewsets

from uploader.models import Document, Image
from uploader.serializers import DocumentUploadSerializer, ImageSerializer, ImageUploadSerializer


class CreateViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    pass


class DocumentUploadViewSet(CreateViewSet):
    queryset = Document.objects.all()  #  pylint: disable=no-member
    serializer_class = DocumentUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]


class ImageUploadViewSet(mixins.RetrieveModelMixin, CreateViewSet):
    queryset = Image.objects.all()  #  pylint: disable=no-member
    serializer_class = ImageUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ImageSerializer
        return super().get_serializer_class()
