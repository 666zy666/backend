from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, Address


class UserProfileSerializer(serializers.ModelSerializer):
    """个人信息查看与编辑序列化器（含手机号/头像）"""
    phone = serializers.CharField(source='userprofile.phone', default='', allow_blank=True, required=False)
    avatar = serializers.URLField(source='userprofile.avatar', default='', allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'avatar']
        read_only_fields = ['id', 'username']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "两次新密码不一致"})
        return data


class AddressSerializer(serializers.ModelSerializer):
    """收货地址序列化器"""
    class Meta:
        model = Address
        fields = ['id', 'recipient_name', 'phone', 'province', 'city', 'district', 'detail', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']
