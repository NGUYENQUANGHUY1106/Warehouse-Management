# Kiến trúc StorePro

## 1. Phân tích nghiệp vụ

`Store` là tenant nghiệp vụ. Người dùng tham gia một hoặc nhiều store thông
qua `StoreMember`; mỗi membership có một `Role`, và role nhận nhiều
`Permission`. Dữ liệu danh mục, sản phẩm, khách hàng, nhà cung cấp, kho và chứng
từ đều thuộc một store.

Sản phẩm không chứa số tồn. Mỗi cặp kho–sản phẩm–biến thể có một dòng
`Inventory`; sản phẩm không có biến thể dùng `variant = NULL`. Tồn khả dụng
được tính động bằng `quantity_on_hand - quantity_reserved`, tránh lưu dữ liệu
trùng. Mọi thay đổi tồn tạo `InventoryTransaction` để truy vết.

Phiếu nhập hoàn tất làm tăng tồn. Phiếu xuất hoàn tất làm giảm tồn; chuyển kho
tạo đồng thời `TRANSFER_OUT` ở kho nguồn và `TRANSFER_IN` ở kho đích. Các thao
tác dùng `transaction.atomic()` và `select_for_update()` nên hai request đồng
thời không thể cùng tiêu thụ một lượng tồn.

Checkout tạo `InventoryReservation` giữ hàng 5 phút. Tạo đơn không trừ tồn vật
lý; hoàn tất đơn mới consume reservation. Hủy đơn hoặc hết hạn sẽ nhả lượng
giữ. Constraint bảo đảm tồn và tiền không âm, quantity dương, và
`quantity_reserved <= quantity_on_hand`.

`Customer.total_orders` và `Customer.total_spent` được tính động từ đơn hàng đã
hoàn tất để không bị lệch dữ liệu. `Supplier.debt` được tính từ sổ giao dịch
công nợ. Nếu dữ liệu sau này rất lớn, các số này nên được cache bằng bảng tổng
hợp/materialized view và cập nhật trong cùng transaction, không thêm cột thủ
công thiếu cơ chế đồng bộ.

`Product`, `Supplier`, `Customer` dùng soft delete (`is_active`, `deleted_at`).
Các ForeignKey lịch sử dùng `PROTECT`; item chỉ `CASCADE` theo chứng từ cha.
`AuditLog` là append-only: model, queryset, API và admin đều chặn sửa/xóa.

## 2. Django apps

| App | Trách nhiệm |
| --- | --- |
| `core` | Abstract UUID và timestamp model |
| `accounts` | Custom User, profile, role, permission, membership, seed |
| `stores` | Tenant/gian hàng |
| `warehouses` | Kho và quản lý kho |
| `products` | Danh mục, thương hiệu, sản phẩm, ảnh, biến thể, thuộc tính |
| `suppliers` | Nhà cung cấp và sổ công nợ |
| `customers` | Nhóm khách và khách hàng |
| `inventory` | Tồn kho, ledger, reservation, cảnh báo, service khóa dòng |
| `stock_in` | Phiếu nhập và service hoàn tất nhập |
| `stock_out` | Phiếu xuất/chuyển kho và service hoàn tất xuất |
| `orders` | Đơn hàng, item, timeline và service vòng đời đơn |
| `payments` | Giao dịch thanh toán |
| `audit_logs` | Nhật ký bất biến |
| `notifications` | Thông báo theo user/store |
| `reports` | API tổng hợp báo cáo |
| `dashboard`, `staff`, `settings_app` | Các trang giao diện hiện có |

## 3. Cấu trúc thư mục

```text
ManageStorage/
├── apps/
│   ├── core/
│   ├── accounts/
│   │   └── management/commands/seed_data.py
│   ├── stores/
│   ├── warehouses/
│   ├── products/
│   ├── suppliers/
│   ├── customers/
│   ├── inventory/
│   │   ├── management/commands/expire_reservations.py
│   │   └── services.py
│   ├── stock_in/services.py
│   ├── stock_out/services.py
│   ├── orders/services.py
│   ├── payments/
│   ├── reports/
│   ├── audit_logs/
│   └── notifications/
├── inventory_project/
│   ├── settings.py
│   ├── urls.py
│   └── api_urls.py
├── docs/ARCHITECTURE.md
├── templates/
├── static/
├── .env.example
├── requirements.txt
└── manage.py
```

Mỗi app dữ liệu có `models.py`, `serializers.py`, `api.py`, `admin.py` và thư
mục `migrations/` riêng.

## 4. ERD tổng thể

```text
User
 ├── UserProfile (1:1)
 └── StoreMember (1:N) ── Store (N:1)
                         └── Role (N:1) ── Permission (N:N)

Store
 ├── Warehouse
 │    └── Inventory
 │         ├── InventoryTransaction
 │         ├── InventoryReservation ── Order
 │         └── InventoryAlert
 │
 ├── Category (self parent/children)
 ├── Brand
 ├── Product
 │    ├── ProductImage
 │    ├── ProductVariant
 │    │    └── VariantAttribute ── AttributeValue ── Attribute
 │    └── Inventory (qua Warehouse)
 │
 ├── Supplier
 │    ├── StockIn
 │    │    └── StockInItem ── Product/ProductVariant
 │    └── SupplierDebtTransaction
 │
 ├── CustomerGroup
 │    └── Customer
 │         ├── Order
 │         └── StockOut
 │
 ├── Order
 │    ├── OrderItem ── Product/ProductVariant
 │    ├── Payment
 │    ├── OrderStatusHistory
 │    └── InventoryReservation
 │
 ├── StockOut
 │    └── StockOutItem ── Product/ProductVariant
 │
 ├── AuditLog
 └── Notification
```

## 5. Quan hệ và ràng buộc quan trọng

- `Store + SKU`, `Store + code`, `Store + slug` là unique theo tenant.
- Inventory dùng hai partial unique constraint để xử lý đúng cả variant NULL
  và variant cụ thể trong PostgreSQL.
- Mỗi product chỉ có tối đa một ảnh `is_primary=True`.
- Mỗi order chỉ có một reservation ACTIVE cho một product/variant.
- `ProductVariant → Product`, item → product/variant và warehouse → store được
  kiểm tra ở model/service.
- Số tiền dùng `DecimalField`; quantity dùng số nguyên dương và CheckConstraint.
- Các cột tra cứu `code`, `sku`, `barcode`, `status`, thời gian và các khóa báo
  cáo có index.

## 6. Luồng chống race condition

```text
Request checkout
  → transaction.atomic
  → SELECT Inventory ... FOR UPDATE (chỉ khóa dòng Inventory)
  → kiểm tra on_hand - reserved
  → tạo Reservation ACTIVE, expires_at = now + 5 phút
  → tăng reserved, ghi transaction RESERVE

Thanh toán/hoàn tất
  → khóa Order + Reservation + Inventory
  → kiểm tra reservation còn hạn và tồn đủ
  → on_hand -= quantity; reserved -= quantity
  → reservation = CONSUMED
  → ghi transaction SALE + status history + AuditLog

Hủy/hết hạn
  → khóa Reservation + Inventory
  → reserved -= quantity
  → reservation = RELEASED/EXPIRED
  → ghi transaction RELEASE
```

UUID được dùng cho khóa chính nghiệp vụ vì phù hợp API đa tenant, khó đoán ID và
dễ hợp nhất dữ liệu giữa các hệ thống. Các bảng Django nội bộ vẫn theo mặc định
của framework.
