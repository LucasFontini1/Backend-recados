from rest_framework import serializers
from core.models import Question

class QuestionSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    author_email = serializers.EmailField(source='author.email', read_only=True)
    answered_by_name = serializers.CharField(source='answered_by.name', read_only=True, default=None)

    class Meta:
        model = Question
        fields = ['id', 'subject', 'text', 'author_name', 'author_email', 'created_at',
                  'answer', 'answered_at', 'answered_by_name']
        read_only_fields = ['id', 'author_name', 'author_email', 'created_at',
                            'answer', 'answered_at', 'answered_by_name']
