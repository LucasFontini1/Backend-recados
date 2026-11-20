from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, obj):
        return sorted(obj.get_all_permissions())

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups', 'permissions']
        depth = 1

class UserGroupUpdateSerializer(serializers.Serializer):
    group = serializers.ChoiceField(choices=['viewer', 'admin'])

    def update(self, instance, validated_data):
        group = Group.objects.get(name=validated_data['group'])
        instance.groups.set([group])
        return instance


class SimpleUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id','name']


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    accept_terms = serializers.BooleanField(write_only=True, required=True)
    accept_privacy = serializers.BooleanField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'accept_terms', 'accept_privacy']

    def validate(self, attrs):
        if attrs.get('accept_terms') is not True:
            raise serializers.ValidationError({'accept_terms': 'É necessário aceitar os Termos de Uso.'})
        if attrs.get('accept_privacy') is not True:
            raise serializers.ValidationError({'accept_privacy': 'É necessário confirmar a leitura da Política de Privacidade.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('accept_terms')
        validated_data.pop('accept_privacy')
        return User.objects.create_user(
            **validated_data,
            legal_accepted_at=timezone.now(),
            terms_version='2026-11-20',
            privacy_version='2026-11-20',
        )
