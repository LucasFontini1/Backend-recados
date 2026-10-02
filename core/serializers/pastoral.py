from rest_framework import serializers

from core.models import Pastoral
from uploader.models import Image
from uploader.serializers.image import ImageSerializer


class PastoralSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    attachment_key = serializers.SlugRelatedField(
        source='image',
        slug_field='attachment_key',
        queryset=Image.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Pastoral
        fields = ['id', 'name', 'image', 'color', 'attachment_key']
        read_only_fields = ['image']


class PastoralListRetrieveSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)

    class Meta:
        model = Pastoral
        fields = ['id', 'name', 'image', 'color']
