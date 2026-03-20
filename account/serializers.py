from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'avatar']
        read_only_fields = ['id']          # 只读 id，其它字段都可修改

    def get_avatar(self, obj):
        request = self.context.get('request')
        try:
            profile = obj.profile
            if profile.avatar:
                return request.build_absolute_uri(profile.avatar) if request else profile.avatar
            return None
        except:
            return None
class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "两次新密码不一致"})
        return data