# 密码登录account/views.py
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
import requests
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from .models import UserProfile, Address
from .serializers import UserProfileSerializer, ChangePasswordSerializer, AddressSerializer
from store.models import Product, Order


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

class UserProfileView(generics.RetrieveUpdateAPIView):
    """个人信息查看与修改"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """修改密码"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data['old_password']

        # 验证旧密码是否正确
        if not user.check_password(old_password):
            return Response({"old_password": "旧密码错误"}, status=status.HTTP_400_BAD_REQUEST)

        new_password = serializer.validated_data['new_password']

        # Django 密码强度验证
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({"new_password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        # 修改密码并保持登录状态
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        return Response({"detail": "密码修改成功"}, status=status.HTTP_200_OK)


# ── 收货地址管理 ──────────────────────────────────────────────

class AddressListCreateView(generics.ListCreateAPIView):
    """收货地址列表 & 新增"""
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """收货地址详情 / 修改 / 删除"""
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class SetDefaultAddressView(APIView):
    """设置默认地址（同一用户仅一个默认）"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        address = Address.objects.filter(pk=pk, user=request.user).first()
        if not address:
            return Response({"detail": "地址不存在"}, status=status.HTTP_404_NOT_FOUND)
        # 取消该用户所有默认地址
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save()
        return Response(AddressSerializer(address).data)


# ── 管理员接口 ────────────────────────────────────────────────

class AdminStatsView(APIView):
    """管理员统计面板"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        order_status_counts = {}
        for code, label in Order.STATUS_CHOICES:
            order_status_counts[code] = Order.objects.filter(status=code).count()
        total_revenue = Order.objects.filter(
            status__in=['completed', 'pending_receipt']
        ).aggregate(total=Sum('price'))['total'] or 0
        return Response({
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "order_status_counts": order_status_counts,
            "total_revenue": str(total_revenue),
        })


class AdminUserListView(generics.ListAPIView):
    """管理员用户列表 & 搜索（用户名/联系方式）"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        keyword = request.query_params.get('keyword', '').strip()
        queryset = User.objects.all().order_by('-date_joined')
        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword) |
                Q(email__icontains=keyword) |
                Q(userprofile__phone__icontains=keyword)
            ).distinct()
        data = []
        for u in queryset:
            profile = getattr(u, 'userprofile', None)
            data.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "phone": profile.phone if profile else '',
                "avatar": profile.avatar if profile else '',
                "is_staff": u.is_staff,
                "is_active": u.is_active,
                "date_joined": u.date_joined,
            })
        return Response(data)


class AdminProductListView(generics.ListAPIView):
    """管理员商品列表 & 搜索（商品名）"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        from store.serializers import ProductSerializer
        keyword = request.query_params.get('keyword', '').strip()
        queryset = Product.objects.all().order_by('-created_at')
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(brand__icontains=keyword) |
                Q(machinery_type__icontains=keyword)
            )
        serializer = ProductSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class AdminOrderListView(generics.ListAPIView):
    """管理员订单列表 & 搜索（订单号/用户名/状态）"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        from store.serializers import OrderSerializer
        keyword = request.query_params.get('keyword', '').strip()
        order_status = request.query_params.get('status', '').strip()
        queryset = Order.objects.all().order_by('-created_at')
        if keyword:
            queryset = queryset.filter(
                Q(id__icontains=keyword) |
                Q(buyer__username__icontains=keyword) |
                Q(seller__username__icontains=keyword)
            )
        if order_status:
            queryset = queryset.filter(status=order_status)
        serializer = OrderSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


        return Response({"detail": "密码修改成功"}, status=status.HTTP_200_OK)