# 密码登录account/views.py
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
import requests
class PasswordLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"detail": "请输入用户名和密码"}, status=400)

        # 验证账号密码
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "用户名或密码错误"}, status=400)

        # 生成或获取 token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user_id": user.id,
            "username": user.username
        })

#账号密码注册
class RegisterView(APIView):
    permission_classes = [AllowAny]   # 关键！允许未登录访问
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        phone = request.data.get('phone', '')

        if not all([username, password, password2]):
            return Response({"detail": "请填写完整信息"}, status=400)

        if password != password2:
            return Response({"detail": "两次密码不一致"}, status=400)

        if len(password) < 6:
            return Response({"detail": "密码至少6位"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"detail": "用户名已存在"}, status=400)

        # 创建用户
        user = User.objects.create_user(username=username, password=password)
        user.save()

        # 生成 token（注册即登录）
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "username": username,
            "message": "注册成功，已自动登录"
        }, status=201)

# 微信登录account/views.py
class WeChatLoginView(APIView):
    permission_classes = [AllowAny]  # 允许未登录访问

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({"detail": "缺少code"}, status=400)

        # 微信官方接口换取 openid
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": 'wxb99c847d498cfbbc',       # ← 你的小程序AppID
            "secret": '8098568c7622223a6b633e4a9b995226',  # ← 你的AppSecret
            "js_code": code,
            "grant_type": "authorization_code"
        }
        wx_resp = requests.get(url, params=params).json()

        if wx_resp.get('errcode'):
            return Response({"detail": "微信授权失败: " + wx_resp.get('errmsg', '')}, status=400)

        openid = wx_resp['openid']

        # 根据 openid 获取或创建用户
        user, created = User.objects.get_or_create(
            username=f"wx_{openid[-8:]}",  # 避免用户名重复，用 openid 后8位
            defaults={'is_active': True}
        )
        if created:
            user.set_unusable_password()
            user.save()

        # 生成 token
        token, _ = Token.objects.get_or_create(user=user)

        # 返回数据（包含用户名，可扩展从微信获取真实昵称）
        return Response({
            "token": token.key,
            "username": user.username,  # 后端用户名
            "nickName": user.username,  # 初始为用户名，后续可通过 getUserInfo 更新真实昵称
            "message": "微信登录成功"
        })

class UpdateUserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        nickName = request.data.get('nickName')
        avatarUrl = request.data.get('avatarUrl')

        if not nickName:
            return Response({"detail": "缺少昵称"}, status=400)

        user = request.user
        user.username = nickName  # 或保存到 profile 模型
        user.save()

        return Response({"message": "用户信息更新成功"})