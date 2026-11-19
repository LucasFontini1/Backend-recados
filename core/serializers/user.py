from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
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

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
