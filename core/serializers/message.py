from rest_framework import serializers

from core.models import Message
from uploader.models.image import Image
from uploader.serializers.image import ImageSerializer


class MessageSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    attachment_key = serializers.SlugRelatedField(
            source='image',
            slug_field='attachment_key',
            queryset=Image.objects.all(),
            required=False,
            allow_null=True,
            write_only=True,
    )
    autor = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Message
        fields = ['id', 'title', 'text', 'autor', 'image', 'event_date', 'created_at', 'pastoral', 'category', 'attachment_key']
        read_only_fields = ['id', 'created_at']


class MessageListRetrieveSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'title', 'text', 'image', 'event_date', 'created_at', 'pastoral', 'category']
        read_only_fields = ['id', 'created_at']
