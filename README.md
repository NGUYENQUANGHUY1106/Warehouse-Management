# StorePro — Quản lý gian hàng, kho hàng và đơn hàng

Backend Django/DRF sử dụng duy nhất PostgreSQL cho nghiệp vụ đa gian hàng:
sản phẩm, kho, nhập/xuất, giữ tồn khi checkout, đơn hàng, thanh toán, khách
hàng, nhà cung cấp, phân quyền, báo cáo, thông báo và Audit Log.

Thiết kế chi tiết và ERD nằm tại [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tiến độ chức năng

Quy ước trạng thái:

- `HOÀN THÀNH`: backend, phân quyền và kiểm thử đã chạy thành công.
- `BACKEND XONG`: model/API/service đã có nhưng giao diện vẫn dùng dữ liệu mẫu.
- `CHƯA LÀM`: chưa kết nối thành luồng sử dụng hoàn chỉnh.

| STT | Chức năng | Trạng thái | Ghi chú |
| ---: | --- | --- | --- |
| 1 | PostgreSQL và database schema | HOÀN THÀNH | Migration đã chạy trên `ManagerStorage.public` |
| 2 | Custom User, đăng nhập, đăng xuất | HOÀN THÀNH | Hỗ trợ session và API token |
| 3 | RBAC Admin/nhân viên | HOÀN THÀNH | 5 role, 35 permission, chặn API và trang HTML |
| 4 | Phân tách dữ liệu theo gian hàng | HOÀN THÀNH | Queryset và thao tác ghi bị giới hạn theo StoreMember |
| 5 | Sản phẩm, danh mục, thương hiệu, ảnh, biến thể | HOÀN THÀNH | CRUD thật, tìm kiếm/lọc, upload ảnh, biến thể và soft-delete |
| 6 | Nhà cung cấp và khách hàng | BACKEND XONG | **Chức năng tiếp theo:** kết nối CRUD vào giao diện thật |
| 7 | Nhập kho | BACKEND XONG | Service hoàn tất nhập và lịch sử kho đã có |
| 8 | Xuất kho/chuyển kho | BACKEND XONG | Đã khóa dòng và chặn xuất vượt tồn |
| 9 | Tồn kho và reservation 5 phút | BACKEND XONG | Service và test đã có, giao diện chưa kết nối API |
| 10 | Đơn hàng và thanh toán | BACKEND XONG | Service vòng đời đơn đã có, giao diện chưa kết nối API |
| 11 | Báo cáo | BACKEND XONG | API tổng hợp đã có, biểu đồ đang dùng dữ liệu mẫu |
| 12 | Audit Log | BACKEND XONG | Append-only; cần bổ sung tự động cho toàn bộ CRUD thường |
| 13 | Notification | BACKEND XONG | Model/API đã có, chưa có tác vụ tự sinh thông báo |

### Thứ tự phát triển tiếp theo

```text
CRUD nhà cung cấp và khách hàng
→ giao diện nhập kho
→ giao diện xuất kho
→ giao diện tồn kho
→ đơn hàng và thanh toán
→ báo cáo thật
→ thông báo tự động và hoàn thiện Audit Log
```

Sau mỗi module hoàn thành phải cập nhật bảng này, ghi endpoint/action mới và
chạy lại `python manage.py test` trước khi chuyển sang module tiếp theo.

### Module sản phẩm đã hoàn thành

Giao diện `/products/` đã bỏ dữ liệu mẫu và đọc trực tiếp từ PostgreSQL. Module
hiện hỗ trợ:

- Danh sách có phân trang, tìm theo SKU/barcode/tên, lọc danh mục/trạng thái và
  sắp xếp theo tên, giá hoặc tồn kho.
- KPI tổng sản phẩm, đang bán, sắp hết và hết hàng lấy từ database.
- Thêm, xem chi tiết và cập nhật sản phẩm bằng Django ModelForm.
- Quản lý danh mục cha–con và thương hiệu tại `/products/catalog/`.
- Upload nhiều ảnh, chọn ảnh chính tự động và xóa ảnh.
- Thêm/xóa biến thể theo SKU, barcode, giá và trạng thái.
- Soft-delete sản phẩm: chuyển sang `ARCHIVED`, đặt `deleted_at`, không xóa lịch
  sử tồn kho/giao dịch; có chức năng khôi phục.
- Áp dụng `product.view/create/update/delete`, giới hạn theo store và ghi
  Audit Log cho cả giao diện lẫn API.

Các route giao diện:

```text
GET  /products/
GET  /products/new/
POST /products/new/
GET  /products/{id}/
GET  /products/{id}/edit/
POST /products/{id}/edit/
POST /products/{id}/delete/
POST /products/{id}/restore/
POST /products/{id}/images/add/
POST /products/{id}/images/{image_id}/delete/
POST /products/{id}/variants/add/
POST /products/{id}/variants/{variant_id}/delete/
GET  /products/catalog/
```

## Công nghệ

- Python 3.11+
- Django 5.2
- Django REST Framework
- PostgreSQL 18 (database `ManagerStorage`)
- `django-environ`, `psycopg`, Pillow

Project không có cấu hình SQLite. Django Model và migration là source of truth
cho toàn bộ schema.

## Cài đặt trên Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Mở `.env` và điền thông tin PostgreSQL:

```dotenv
DB_NAME=ManagerStorage
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
SEED_ADMIN_PASSWORD=your-strong-admin-password
SEED_STAFF_PASSWORD=your-strong-staff-password
```

Database `ManagerStorage` phải tồn tại và user PostgreSQL phải có quyền tạo,
sửa bảng trong schema `public`. Password chỉ nằm trong `.env`; file này đã
được `.gitignore` loại trừ.

## Migration và dữ liệu mẫu

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

`seed_data` là idempotent: có thể chạy lại mà không nhân đôi dữ liệu. Có thể
đặt mật khẩu quản trị và nhân viên bằng biến môi trường hoặc tham số:

```powershell
$env:SEED_ADMIN_PASSWORD = "a-strong-password"
$env:SEED_STAFF_PASSWORD = "another-strong-password"
python manage.py seed_data --admin-username admin --admin-email admin@storepro.vn --staff-password "another-strong-password"
```

Nếu không truyền password, dữ liệu phát triển dùng `Admin@123456` và
`Staff@123456`; cần đổi ngay trước khi triển khai thật.

## Đăng nhập và tài khoản mẫu

Form `/login/` đã kết nối với Django Authentication thật, chấp nhận email hoặc
username. Đăng nhập thành công tạo session, chọn StoreMember đầu tiên làm gian
hàng hoạt động và ghi `AuditLog.LOGIN`. Nút đăng xuất gửi POST đến
`/login/logout/`, hủy session và ghi `AuditLog.LOGOUT`.

Các trang nghiệp vụ đều yêu cầu đăng nhập. Nếu chưa đăng nhập, Django chuyển về
`/login/?next=...`; nếu đã đăng nhập nhưng thiếu quyền, server trả HTTP `403`.

`python manage.py seed_data` tạo các tài khoản phát triển sau:

| Username | Email | Mật khẩu mặc định | Vai trò |
| --- | --- | --- | --- |
| `admin` | `admin@storepro.vn` | `Admin@123456` | Admin |
| `warehouse` | `warehouse@storepro.vn` | `Staff@123456` | Quản lý kho |
| `sales` | `sales@storepro.vn` | `Staff@123456` | Nhân viên bán hàng |
| `accountant` | `accountant@storepro.vn` | `Staff@123456` | Kế toán |
| `viewer` | `viewer@storepro.vn` | `Staff@123456` | Viewer |

Không có đăng ký công khai. Admin tạo tài khoản qua `/api/users/`, gán tài khoản
vào gian hàng qua `/api/store-members/`, sau đó chọn role. Điều này tránh người
lạ tự đăng ký vào hệ thống nội bộ.

## RBAC và phân tách dữ liệu theo gian hàng

RBAC đi theo chuỗi quan hệ:

```text
User → StoreMember → Store + Role → Permission
```

Mỗi action API kiểm tra một permission code trước khi chạy. Sau khi có quyền,
queryset tiếp tục bị lọc theo gian hàng hoạt động. Người dùng không thể đọc ID
của store khác và cũng không thể gửi payload để ghi dữ liệu sang store khác.

Superuser Django được phép quản trị toàn hệ thống. Một người có role `Admin`
trong store chỉ có quyền bên trong store đó. `is_staff` là quyền vào Django
Admin và chỉ superuser được thay đổi qua API; nó không thay thế StorePro RBAC.

### Ma trận quyền mặc định

| Nhóm chức năng | Admin | Quản lý kho | Bán hàng | Kế toán | Viewer |
| --- | :---: | :---: | :---: | :---: | :---: |
| Gian hàng | Quản lý | Xem | Xem | Xem | Xem |
| Kho | Quản lý | Quản lý | Xem | — | Xem |
| Sản phẩm | CRUD | Tạo/sửa/xem | Xem | — | Xem |
| Tồn kho | Xem/điều chỉnh | Xem/điều chỉnh | Xem | — | Xem |
| Nhập kho | Toàn quyền | Tạo/xem/hoàn tất | — | — | — |
| Xuất kho | Toàn quyền | Tạo/xem/hoàn tất | — | — | — |
| Đơn hàng | Toàn quyền | — | Tạo/xem/cập nhật/hủy/hoàn tất | Xem | Xem |
| Khách hàng | Quản lý | — | Quản lý | — | Xem |
| Nhà cung cấp/công nợ | Quản lý | Quản lý | — | Quản lý | Xem |
| Thanh toán | Quản lý | — | Quản lý | Quản lý | — |
| Nhân viên/role | Quản lý | — | — | — | — |
| Báo cáo | Xem | Xem | — | Xem | Xem |
| Audit Log | Xem | — | — | Xem | — |

Admin có toàn bộ permission được seed. Các permission chi tiết gồm:

```text
store.view, store.manage
warehouse.view, warehouse.manage
product.view, product.create, product.update, product.delete
inventory.view, inventory.adjust
stockin.view, stockin.create, stockin.complete
stockout.view, stockout.create, stockout.complete
order.view, order.create, order.update, order.cancel, order.complete
customer.view, customer.manage
supplier.view, supplier.manage
payment.view, payment.manage
user.view, user.manage
role.view, role.manage
report.view, audit.view
notification.view, notification.manage
```

Các file triển khai chính:

- `apps/accounts/rbac.py`: permission class, tenant queryset và decorator HTML.
- `apps/accounts/context_processors.py`: role/quyền cho menu giao diện.
- `apps/accounts/views.py`: đăng nhập, đăng xuất và đổi gian hàng.
- `apps/accounts/management/commands/seed_data.py`: permission/role/user mẫu.
- Mỗi `apps/*/api.py`: ánh xạ action sang permission code.

### Chọn gian hàng hoạt động

Trên giao diện, nếu user thuộc nhiều gian hàng, thanh trên cùng hiển thị hộp
chọn store. API chọn store bằng một trong hai cách:

```http
X-Store-ID: <uuid-cua-store>
```

hoặc khi đọc danh sách:

```text
GET /api/products/?store=<uuid-cua-store>
```

Store được yêu cầu phải có StoreMember `ACTIVE` của chính user. Khi gửi JSON
ghi dữ liệu cho user có nhiều store, nên luôn gửi `X-Store-ID`.

Sau migration, trong pgAdmin chọn:
`ManagerStorage → Schemas → public → Tables → Refresh`.

## Endpoint chính

Đăng nhập lấy token:

```http
POST /api/auth/
Content-Type: application/json

{"username": "admin", "password": "..."}
```

Có thể dùng email thay cho username. Response trả token, user, store hiện hành,
role và danh sách permission:

```json
{
  "token": "...",
  "user": {"id": "...", "username": "sales"},
  "active_store": "...",
  "role": "Nhân viên bán hàng",
  "permissions": ["customer.manage", "order.create", "product.view"]
}
```

Gửi token bằng header `Authorization: Token <token>`. Thu hồi token:

```http
DELETE /api/auth/
Authorization: Token <token>
```

Quy ước phản hồi bảo mật:

- `401`: chưa đăng nhập hoặc token không hợp lệ.
- `403`: đã đăng nhập nhưng thiếu role/permission hoặc không thuộc store.
- `404`: object không nằm trong queryset của store hiện hành.

- `/api/stores/`, `/api/warehouses/`
- `/api/products/`, `/api/product-images/`, `/api/product-variants/`,
  `/api/categories/`, `/api/brands/`
- `/api/inventory/`, `/api/inventory-transactions/`,
  `/api/inventory-reservations/`, `/api/inventory-alerts/`
- `/api/stock-in/`, `/api/stock-out/`, `/api/orders/`, `/api/payments/`
- `/api/customers/`, `/api/customer-groups/`
- `/api/suppliers/`, `/api/supplier-debts/`
- `/api/users/`, `/api/roles/`, `/api/permissions/`, `/api/store-members/`
- `/api/reports/`, `/api/audit-logs/`, `/api/notifications/`

Các action nghiệp vụ:

```text
POST /api/stock-in/{id}/complete/
POST /api/stock-out/{id}/complete/
POST /api/orders/{id}/confirm/
POST /api/orders/{id}/complete/
POST /api/orders/{id}/cancel/
POST /api/inventory/{id}/adjust/
```

Điều chỉnh tồn kho nhận payload:

```json
{"quantity_after": 25, "note": "Kiểm kê cuối ngày"}
```

Inventory API không cho PATCH trực tiếp số lượng. Mọi thay đổi phải đi qua
service để khóa dòng, kiểm tra tồn và ghi `InventoryTransaction`/`AuditLog`.

## Giữ hàng 5 phút

Khi tạo đơn, hệ thống tăng `quantity_reserved` chứ chưa trừ
`quantity_on_hand`. Khi hoàn tất đơn, reservation được consume và cả hai giá
trị được giảm trong một transaction. Chạy lệnh sau định kỳ mỗi phút bằng Task
Scheduler, cron hoặc worker:

```powershell
python manage.py expire_reservations
```

Lệnh nhả tất cả reservation `ACTIVE` đã quá `expires_at` và ghi lịch sử kho.

## Admin và giao diện hiện có

- Django Admin: `http://127.0.0.1:8000/admin/`
- Giao diện template: `http://127.0.0.1:8000/`
- API browsable: `http://127.0.0.1:8000/api/`

Menu HTML tự ẩn module mà role không có quyền. Server vẫn kiểm tra lại quyền ở
view/API; việc ẩn menu chỉ hỗ trợ trải nghiệm, không phải lớp bảo mật duy nhất.

Các trang bảng/biểu đồ ngoài màn hình đăng nhập vẫn là UI skeleton; CRUD dữ
liệu thật hiện thực hiện qua DRF API hoặc Django Admin.

## Kiểm tra nhanh

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Bộ test hiện có 15 test, kiểm tra đăng nhập session, token login, lọc dữ liệu
theo store, Admin không thể ghi chéo store, nhân viên bị chặn endpoint ngoài
quyền, CRUD sản phẩm/danh mục/biến thể/ảnh, soft-delete, giữ/nhả tồn kho, xuất
vượt tồn và Audit Log bất biến.
