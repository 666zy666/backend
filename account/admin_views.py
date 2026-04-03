"""
Admin management API views.

All views require the request user to be is_staff=True (IsAdminUser).
The only exception is AdminAuthLoginView which is open (AllowAny).
"""
import logging
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now as tz_now

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile
from store.models import Product, Order, Category, Banner
from store.serializers import ProductSerializer, OrderSerializer, BannerSerializer

logger = logging.getLogger(__name__)


# ── Pagination helper ─────────────────────────────────────────────────────────

class AdminPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "results": data,
        })


# ── Auth ──────────────────────────────────────────────────────────────────────

class AdminAuthLoginView(APIView):
    """POST /api/admin/auth/login/ — admin login (no auth required)."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        if not username or not password:
            return Response({"detail": "请输入用户名和密码"}, status=400)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "用户名或密码错误"}, status=400)
        if not user.is_staff:
            return Response({"detail": "无管理员权限"}, status=403)

        token, _ = Token.objects.get_or_create(user=user)
        logger.info("Admin login: user=%s id=%s", user.username, user.id)
        return Response({
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        })


class AdminAuthMeView(APIView):
    """GET /api/admin/auth/me/ — current admin info."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined,
        })


# ── Dashboard ─────────────────────────────────────────────────────────────────

class AdminDashboardOverviewView(APIView):
    """GET /api/admin/dashboard/overview"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.localdate()
        today_start = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        today_end = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.max.time())
        )

        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()

        today_users = User.objects.filter(date_joined__range=(today_start, today_end)).count()
        today_orders = Order.objects.filter(created_at__range=(today_start, today_end)).count()
        today_revenue = (
            Order.objects.filter(
                created_at__range=(today_start, today_end),
                status__in=[Order.STATUS_COMPLETED, Order.STATUS_PENDING_RECEIPT,
                            Order.STATUS_PENDING_SHIPMENT],
            ).aggregate(total=Sum('price'))['total'] or 0
        )

        total_revenue = (
            Order.objects.filter(
                status__in=[Order.STATUS_COMPLETED, Order.STATUS_PENDING_RECEIPT]
            ).aggregate(total=Sum('price'))['total'] or 0
        )

        order_status_counts = {}
        for code, _label in Order.STATUS_CHOICES:
            order_status_counts[code] = Order.objects.filter(status=code).count()

        return Response({
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "today_new_users": today_users,
            "today_orders": today_orders,
            "today_revenue": str(today_revenue),
            "total_revenue": str(total_revenue),
            "order_status_counts": order_status_counts,
        })


class AdminDashboardTrendView(APIView):
    """GET /api/admin/dashboard/trend/ — last-7-day order trend."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.localdate()
        trend = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_start = timezone.make_aware(
                timezone.datetime.combine(day, timezone.datetime.min.time())
            )
            day_end = timezone.make_aware(
                timezone.datetime.combine(day, timezone.datetime.max.time())
            )
            qs = Order.objects.filter(created_at__range=(day_start, day_end))
            order_count = qs.count()
            revenue = (
                qs.filter(
                    status__in=[
                        Order.STATUS_COMPLETED,
                        Order.STATUS_PENDING_RECEIPT,
                        Order.STATUS_PENDING_SHIPMENT,
                    ]
                ).aggregate(total=Sum('price'))['total'] or 0
            )
            trend.append({
                "date": str(day),
                "order_count": order_count,
                "revenue": str(revenue),
            })
        return Response({"trend": trend})


# ── Users ─────────────────────────────────────────────────────────────────────

class AdminUserListView(APIView):
    """GET /api/admin/users/ — list with pagination & filters.
       POST /api/admin/users/ — create a new user.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        keyword = request.query_params.get('keyword', '').strip()
        status_filter = request.query_params.get('status', '').strip()

        queryset = User.objects.all().order_by('-date_joined')
        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword) |
                Q(email__icontains=keyword) |
                Q(userprofile__phone__icontains=keyword)
            ).distinct()
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        paginator = AdminPagination()
        page_qs = paginator.paginate_queryset(queryset, request)

        data = []
        for u in page_qs:
            profile = getattr(u, 'userprofile', None)
            avatar_url = ''
            if profile and profile.avatar:
                try:
                    avatar_url = request.build_absolute_uri(profile.avatar.url)
                except Exception:
                    avatar_url = ''
            data.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "phone": profile.phone if profile else '',
                "avatar": avatar_url,
                "is_staff": u.is_staff,
                "is_active": u.is_active,
                "date_joined": u.date_joined,
            })
        return paginator.get_paginated_response(data)

    def post(self, request):
        """POST /api/admin/users/ — create a new user."""
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        email = request.data.get('email', '').strip()
        phone = request.data.get('phone', '').strip()
        is_staff = request.data.get('is_staff', False)

        if not username:
            return Response({"detail": "用户名不能为空"}, status=400)
        if not password:
            return Response({"detail": "密码不能为空"}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "用户名已存在"}, status=400)

        if isinstance(is_staff, str):
            is_staff = is_staff.lower() in ('true', '1', 'yes')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_staff=bool(is_staff),
        )
        if phone:
            UserProfile.objects.update_or_create(
                user=user, defaults={'phone': phone}
            )
        logger.info("Admin %s created user id=%s", request.user.username, user.id)
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": phone,
            "is_staff": user.is_staff,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
        }, status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    """GET/PATCH/DELETE /api/admin/users/{id}/"""
    permission_classes = [IsAdminUser]

    def _serialize_user(self, user, request):
        profile = getattr(user, 'userprofile', None)
        avatar_url = ''
        if profile and profile.avatar:
            try:
                avatar_url = request.build_absolute_uri(profile.avatar.url)
            except Exception:
                avatar_url = ''
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": profile.phone if profile else '',
            "avatar": avatar_url,
            "is_staff": user.is_staff,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
        }

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return Response(self._serialize_user(user, request))

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        changed = []

        is_active = request.data.get('is_active')
        if is_active is not None:
            # Accept both JSON booleans and form string values
            if isinstance(is_active, str):
                is_active = is_active.lower() not in ('false', '0', 'no', '')
            user.is_active = bool(is_active)
            changed.append('is_active')

        is_staff = request.data.get('is_staff')
        if is_staff is not None:
            if isinstance(is_staff, str):
                is_staff = is_staff.lower() not in ('false', '0', 'no', '')
            user.is_staff = bool(is_staff)
            changed.append('is_staff')

        email = request.data.get('email')
        if email is not None:
            user.email = email.strip()
            changed.append('email')

        new_username = request.data.get('username')
        if new_username is not None:
            new_username = new_username.strip()
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exclude(pk=pk).exists():
                    return Response({"detail": "用户名已存在"}, status=400)
                user.username = new_username
                changed.append('username')

        password = request.data.get('password')
        if password:
            user.set_password(password)
            changed.append('password')

        if changed:
            user.save(update_fields=changed)
            logger.info(
                "Admin %s updated user id=%s fields=%s",
                request.user.username, pk, changed
            )

        # Update phone if provided
        phone = request.data.get('phone')
        if phone is not None:
            UserProfile.objects.update_or_create(
                user=user, defaults={'phone': phone.strip()}
            )

        return Response({
            "detail": "更新成功",
            **self._serialize_user(user, request),
        })

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            return Response({"detail": "不能删除当前登录账号"}, status=400)
        user_id = user.id
        username = user.username
        user.delete()
        logger.info("Admin %s deleted user id=%s username=%s", request.user.username, user_id, username)
        return Response({"detail": "用户已删除"}, status=status.HTTP_200_OK)


# ── Products ──────────────────────────────────────────────────────────────────

class AdminProductListView(APIView):
    """GET /api/admin/products/ — list with pagination & filters."""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        keyword = request.query_params.get('keyword', '').strip()
        category = request.query_params.get('category', '').strip()
        status_filter = request.query_params.get('status', '').strip()

        queryset = Product.objects.all().order_by('-created_at')
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(brand__icontains=keyword) |
                Q(machinery_type__icontains=keyword)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        paginator = AdminPagination()
        page_qs = paginator.paginate_queryset(queryset, request)
        serializer = ProductSerializer(page_qs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """POST /api/admin/products/ — create product."""
        serializer = ProductSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save(seller=request.user)
        images_data = request.FILES.getlist('images')
        from store.models import ProductImage
        for image in images_data:
            ProductImage.objects.create(product=product, image=image)
        logger.info("Admin %s created product id=%s", request.user.username, product.id)
        return Response(
            ProductSerializer(product, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdminProductDetailView(APIView):
    """GET/PUT/DELETE /api/admin/products/{id}/"""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return Response(ProductSerializer(product, context={'request': request}).data)

    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(
            product, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Admin %s updated product id=%s", request.user.username, pk)
        return Response(serializer.data)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_active = False
        product.save(update_fields=['is_active'])
        logger.info("Admin %s deactivated product id=%s", request.user.username, pk)
        return Response({"detail": "商品已下架（软删除）"}, status=status.HTTP_200_OK)


# ── Orders ────────────────────────────────────────────────────────────────────

class AdminOrderListView(APIView):
    """GET /api/admin/orders/ — list with pagination, keyword, status, date."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        keyword = request.query_params.get('keyword', '').strip()
        status_filter = request.query_params.get('status', '').strip()
        start_date = request.query_params.get('start_date', '').strip()
        end_date = request.query_params.get('end_date', '').strip()

        queryset = Order.objects.all().order_by('-created_at')
        if keyword:
            queryset = queryset.filter(
                Q(order_no__icontains=keyword) |
                Q(buyer__username__icontains=keyword) |
                Q(seller__username__icontains=keyword)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if start_date:
            try:
                from django.utils.dateparse import parse_date
                d = parse_date(start_date)
                if d:
                    queryset = queryset.filter(created_at__date__gte=d)
            except (ValueError, TypeError):
                pass
        if end_date:
            try:
                from django.utils.dateparse import parse_date
                d = parse_date(end_date)
                if d:
                    queryset = queryset.filter(created_at__date__lte=d)
            except (ValueError, TypeError):
                pass

        paginator = AdminPagination()
        page_qs = paginator.paginate_queryset(queryset, request)
        serializer = OrderSerializer(page_qs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class AdminOrderDetailView(APIView):
    """GET/DELETE /api/admin/orders/{id}/"""
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return Response(OrderSerializer(order, context={'request': request}).data)

    def delete(self, request, pk):
        """Cancel order (set status to cancelled). Hard-delete only if already cancelled."""
        order = get_object_or_404(Order, pk=pk)
        if order.status == Order.STATUS_CANCELLED:
            order_id = order.id
            order.delete()
            logger.info("Admin %s hard-deleted cancelled order id=%s", request.user.username, order_id)
            return Response({"detail": "订单已删除"}, status=status.HTTP_200_OK)
        if order.status == Order.STATUS_COMPLETED:
            return Response({"detail": "已完成的订单不可删除"}, status=400)
        order.status = Order.STATUS_CANCELLED
        order.cancel_time = tz_now()
        order.save(update_fields=['status', 'cancel_time'])
        logger.info("Admin %s cancelled order id=%s", request.user.username, pk)
        return Response(OrderSerializer(order, context={'request': request}).data)


class AdminOrderStatusView(APIView):
    """PATCH /api/admin/orders/{id}/status/ — update order status."""
    permission_classes = [IsAdminUser]

    # Admin is allowed to force any transition; validate against known statuses.
    VALID_STATUSES = {choice[0] for choice in Order.STATUS_CHOICES}

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.data.get('status', '').strip()
        if not new_status:
            return Response({"detail": "缺少 status 字段"}, status=400)
        if new_status not in self.VALID_STATUSES:
            return Response(
                {"detail": f"无效状态，可选值：{', '.join(sorted(self.VALID_STATUSES))}"},
                status=400,
            )

        old_status = order.status
        order.status = new_status

        # Keep timestamp fields consistent
        now = tz_now()
        if new_status == Order.STATUS_PENDING_SHIPMENT and not order.paid_at:
            order.paid_at = now
        elif new_status == Order.STATUS_PENDING_RECEIPT and not order.shipped_at:
            order.shipped_at = now
            tracking_number = request.data.get('tracking_number')
            shipping_company = request.data.get('shipping_company')
            if tracking_number is not None:
                order.tracking_number = tracking_number
            if shipping_company is not None:
                order.shipping_company = shipping_company
        elif new_status == Order.STATUS_COMPLETED and not order.completed_at:
            order.completed_at = now
        elif new_status == Order.STATUS_CANCELLED and not order.cancel_time:
            order.cancel_time = now

        order.save()
        logger.info(
            "Admin %s changed order id=%s status %s -> %s",
            request.user.username, pk, old_status, new_status,
        )
        return Response(OrderSerializer(order, context={'request': request}).data)


# ── Banners ───────────────────────────────────────────────────────────────────

class AdminBannerListView(APIView):
    """GET /api/admin/banners/ — list all banners (including inactive).
       POST /api/admin/banners/ — create a banner.
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        is_active_filter = request.query_params.get('is_active', '').strip()
        queryset = Banner.objects.all().order_by('order', 'id')
        if is_active_filter == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active_filter == 'false':
            queryset = queryset.filter(is_active=False)

        paginator = AdminPagination()
        page_qs = paginator.paginate_queryset(queryset, request)
        serializer = BannerSerializer(page_qs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """POST /api/admin/banners/ — create a banner."""
        serializer = BannerSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        banner = serializer.save()
        logger.info("Admin %s created banner id=%s", request.user.username, banner.id)
        return Response(
            BannerSerializer(banner, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdminBannerDetailView(APIView):
    """GET/PUT/DELETE /api/admin/banners/{id}/"""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        return Response(BannerSerializer(banner, context={'request': request}).data)

    def put(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        serializer = BannerSerializer(
            banner, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Admin %s updated banner id=%s", request.user.username, pk)
        return Response(BannerSerializer(banner, context={'request': request}).data)

    def delete(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        banner.delete()
        logger.info("Admin %s deleted banner id=%s", request.user.username, pk)
        return Response({"detail": "轮播图已删除"}, status=status.HTTP_200_OK)
