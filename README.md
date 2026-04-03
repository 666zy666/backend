# 二手交易平台后端 API

Django REST Framework 后端，同时服务**微信小程序端**与**独立 Admin Web 管理后台**。

## 技术栈

- Python 3.x / Django 4+
- Django REST Framework
- Token 认证（`rest_framework.authtoken`）
- SQLite（本地开发） / 可替换为 MySQL/PostgreSQL

---

## 快速启动

```bash
# 安装依赖
pip install django djangorestframework pillow requests django-cors-headers

# 数据库迁移
python manage.py migrate

# 创建管理员账号
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

服务默认监听 `http://127.0.0.1:8000`。

---

## 认证方式

所有需要鉴权的接口均使用 **Token 认证**，在请求头中携带：

```
Authorization: Token <your_token>
```

管理端 Token 通过 `POST /api/admin/auth/login/` 获取（需要 `is_staff=True` 用户）。

---

## 小程序端 API（现有接口，不变）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/account/login/` | 账号密码登录 |
| POST | `/api/account/register/` | 注册 |
| POST | `/api/account/wx-login/` | 微信小程序登录 |
| GET/PUT | `/api/account/profile/` | 个人信息 |
| POST | `/api/account/change-password/` | 修改密码 |
| GET/POST | `/api/account/addresses/` | 收货地址列表/新增 |
| GET/PUT/DELETE | `/api/account/addresses/<id>/` | 地址详情 |
| PATCH | `/api/account/addresses/<id>/set-default/` | 设为默认地址 |
| GET | `/api/store/products/` | 商品列表 |
| GET | `/api/store/products/search/` | 商品搜索 |
| GET/PUT/DELETE | `/api/store/products/<id>/` | 商品详情 |
| GET | `/api/store/banners/` | 轮播图 |
| POST | `/api/store/orders/` | 创建订单 |
| GET | `/api/store/orders/my/` | 我的订单（买家） |
| GET | `/api/store/orders/seller/` | 待处理订单（卖家） |
| GET/PATCH | `/api/store/orders/<id>/` | 订单详情/操作 |
| POST | `/api/store/orders/<id>/pay/` | 订单支付 |
| POST | `/api/store/orders/<id>/cancel/` | 取消订单 |
| POST | `/api/store/orders/<id>/confirm/` | 确认收货 |
| POST | `/api/store/orders/<id>/ship/` | 发货（管理员） |

---

## Admin API

所有 Admin API 均以 `/api/admin/` 为前缀。**除登录接口外，所有接口均要求管理员权限（`is_staff=True`）**。

### 鉴权

#### 管理员登录

```
POST /api/admin/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "yourpassword"
}
```

响应示例：
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "admin",
  "is_staff": true,
  "is_superuser": false
}
```

错误码：
- `400` 用户名或密码错误
- `403` 非管理员账号

#### 获取当前管理员信息

```
GET /api/admin/auth/me/
Authorization: Token <token>
```

---

### 仪表盘

#### 概览统计

```
GET /api/admin/dashboard/overview/
Authorization: Token <token>
```

响应示例：
```json
{
  "total_users": 128,
  "total_products": 356,
  "total_orders": 92,
  "today_new_users": 5,
  "today_orders": 12,
  "today_revenue": "3860.00",
  "total_revenue": "128450.00",
  "order_status_counts": {
    "pending_payment": 10,
    "pending_shipment": 8,
    "pending_receipt": 15,
    "completed": 55,
    "cancelled": 4
  }
}
```

---

### 用户管理

#### 用户列表

```
GET /api/admin/users/?page=1&page_size=10&keyword=alice&status=active
Authorization: Token <token>
```

查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | int | 页码，默认 1 |
| `page_size` | int | 每页条数，默认 10，最大 100 |
| `keyword` | string | 搜索用户名/邮箱/手机号 |
| `status` | string | `active` / `inactive` |

响应示例：
```json
{
  "count": 128,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com",
      "phone": "13800138000",
      "avatar": "http://127.0.0.1:8000/media/avatars/alice.jpg",
      "is_staff": false,
      "is_active": true,
      "date_joined": "2026-01-01T10:00:00Z"
    }
  ]
}
```

#### 用户详情

```
GET /api/admin/users/{id}/
Authorization: Token <token>
```

#### 修改用户

```
PATCH /api/admin/users/{id}/
Authorization: Token <token>
Content-Type: application/json

{
  "is_active": false,
  "is_staff": false
}
```

可更新字段：`is_active`（封禁/解封）、`is_staff`（授予/撤销管理员权限）。

---

### 商品管理

#### 商品列表

```
GET /api/admin/products/?page=1&page_size=10&keyword=挖机&category=3&status=active
Authorization: Token <token>
```

查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | int | 页码 |
| `page_size` | int | 每页条数 |
| `keyword` | string | 搜索标题/品牌/设备类型 |
| `category` | int | 分类 ID |
| `status` | string | `active` / `inactive` |

#### 创建商品

```
POST /api/admin/products/
Authorization: Token <token>
Content-Type: multipart/form-data

title=测试商品&price=999.00&category=1&images=<file>
```

#### 商品详情

```
GET /api/admin/products/{id}/
Authorization: Token <token>
```

#### 修改商品

```
PUT /api/admin/products/{id}/
Authorization: Token <token>
Content-Type: application/json

{
  "title": "新标题",
  "price": "1299.00",
  "is_active": true
}
```

支持部分更新（partial）。

#### 删除商品（软删除/下架）

```
DELETE /api/admin/products/{id}/
Authorization: Token <token>
```

将商品 `is_active` 置为 `false`，不物理删除数据。

响应：
```json
{"detail": "商品已下架（软删除）"}
```

---

### 订单管理

#### 订单列表

```
GET /api/admin/orders/?page=1&page_size=10&keyword=ord_buyer&status=pending_payment&start_date=2026-01-01&end_date=2026-12-31
Authorization: Token <token>
```

查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | int | 页码 |
| `page_size` | int | 每页条数 |
| `keyword` | string | 搜索订单号/买家用户名/卖家用户名 |
| `status` | string | 订单状态（见下表） |
| `start_date` | string | 创建时间起始，格式 `YYYY-MM-DD` |
| `end_date` | string | 创建时间截止，格式 `YYYY-MM-DD` |

订单状态枚举：

| 值 | 说明 |
|----|------|
| `pending_payment` | 待付款 |
| `pending_shipment` | 待发货 |
| `pending_receipt` | 待收货 |
| `completed` | 已完成 |
| `cancelled` | 已取消 |

#### 订单详情

```
GET /api/admin/orders/{id}/
Authorization: Token <token>
```

响应示例：
```json
{
  "id": 1,
  "order_no": "ORD1A2B3C4D5E6F7G8H",
  "buyer": 2,
  "buyer_username": "alice",
  "seller": 3,
  "seller_username": "bob",
  "product": 5,
  "product_title": "二手挖机",
  "product_image": "http://127.0.0.1:8000/media/products/img.jpg",
  "price": "88000.00",
  "status": "pending_shipment",
  "status_display": "待发货",
  "address_snapshot": {
    "recipient_name": "张三",
    "phone": "13800138000",
    "province": "广东",
    "city": "深圳",
    "district": "南山",
    "detail": "科技园路1号"
  },
  "created_at": "2026-03-01T08:00:00Z",
  "paid_at": "2026-03-01T08:30:00Z",
  "shipped_at": null,
  "completed_at": null,
  "cancel_time": null,
  "tracking_number": null,
  "shipping_company": null
}
```

#### 修改订单状态

管理员可强制修改订单为任意合法状态（不受状态机限制）。

```
PATCH /api/admin/orders/{id}/status/
Authorization: Token <token>
Content-Type: application/json

{
  "status": "pending_receipt",
  "tracking_number": "SF1234567890",
  "shipping_company": "顺丰速运"
}
```

`tracking_number` 和 `shipping_company` 仅在 `status=pending_receipt` 时生效。

响应：返回完整订单对象（同订单详情格式）。

错误码：
- `400` 缺少 `status` 字段或无效状态值
- `404` 订单不存在

---

## 典型错误码

| HTTP 状态码 | 场景 |
|-------------|------|
| 400 | 请求参数错误/校验失败 |
| 401 | 未携带 Token 或 Token 无效 |
| 403 | 已认证但权限不足（非管理员） |
| 404 | 资源不存在 |
| 500 | 服务端内部错误 |

---

## 本地调试 Admin 接口

### 1. 创建管理员账号

```bash
python manage.py createsuperuser
# 按提示输入用户名、密码
```

或通过 Django shell 快速创建：

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.create_user('admin', password='admin123')
u.is_staff = True
u.is_superuser = True
u.save()
print('Admin created')
"
```

### 2. 获取 Token

```bash
curl -X POST http://127.0.0.1:8000/api/admin/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. 调用管理接口

```bash
TOKEN="your_token_here"

# 仪表盘概览
curl http://127.0.0.1:8000/api/admin/dashboard/overview/ \
  -H "Authorization: Token $TOKEN"

# 用户列表
curl "http://127.0.0.1:8000/api/admin/users/?page=1&page_size=5" \
  -H "Authorization: Token $TOKEN"

# 修改订单状态
curl -X PATCH http://127.0.0.1:8000/api/admin/orders/1/status/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "pending_receipt", "tracking_number": "SF123456"}'
```

---

## 运行测试

```bash
python manage.py test
```

测试覆盖：
- 权限拦截（未登录/普通用户均被拒绝）
- 管理员登录
- 仪表盘统计接口
- 用户列表/详情/修改
- 商品列表/详情/修改/删除
- 订单列表/详情/状态修改
