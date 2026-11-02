import os
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.accounts.models import Permission, Role, StoreMember, User, UserProfile
from apps.customers.models import Customer, CustomerGroup
from apps.inventory.models import Inventory
from apps.products.models import Category, Product
from apps.stores.models import Store
from apps.suppliers.models import Supplier
from apps.warehouses.models import Warehouse

PERMISSIONS = [
    ("store.view", "store", "Xem gian hàng"),
    ("store.manage", "store", "Cập nhật gian hàng"),
    ("warehouse.view", "warehouse", "Xem kho"),
    ("warehouse.manage", "warehouse", "Quản lý kho"),
    ("product.view", "product", "Xem sản phẩm"),
    ("product.create", "product", "Thêm sản phẩm"),
    ("product.update", "product", "Sửa sản phẩm"),
    ("product.delete", "product", "Xóa sản phẩm"),
    ("inventory.view", "inventory", "Xem tồn kho"),
    ("inventory.adjust", "inventory", "Điều chỉnh tồn kho"),
    ("stockin.create", "stockin", "Tạo phiếu nhập"),
    ("stockin.view", "stockin", "Xem phiếu nhập"),
    ("stockin.complete", "stockin", "Hoàn tất phiếu nhập"),
    ("stockout.create", "stockout", "Tạo phiếu xuất"),
    ("stockout.view", "stockout", "Xem phiếu xuất"),
    ("stockout.complete", "stockout", "Hoàn tất phiếu xuất"),
    ("order.view", "order", "Xem đơn hàng"),
    ("order.create", "order", "Tạo đơn hàng"),
    ("order.update", "order", "Sửa đơn hàng"),
    ("order.cancel", "order", "Hủy đơn hàng"),
    ("order.complete", "order", "Hoàn tất đơn hàng"),
    ("customer.view", "customer", "Xem khách hàng"),
    ("customer.manage", "customer", "Quản lý khách hàng"),
    ("supplier.view", "supplier", "Xem nhà cung cấp"),
    ("supplier.manage", "supplier", "Quản lý nhà cung cấp"),
    ("payment.view", "payment", "Xem thanh toán"),
    ("payment.manage", "payment", "Quản lý thanh toán"),
    ("user.view", "user", "Xem nhân viên"),
    ("user.manage", "user", "Quản lý nhân viên"),
    ("role.view", "role", "Xem vai trò và quyền"),
    ("role.manage", "role", "Quản lý vai trò và quyền"),
    ("report.view", "report", "Xem báo cáo"),
    ("audit.view", "audit", "Xem Audit Log"),
    ("notification.view", "notification", "Xem thông báo"),
    ("notification.manage", "notification", "Quản lý thông báo"),
]


class Command(BaseCommand):
    help = "Tạo dữ liệu khởi tạo cho StorePro."

    def add_arguments(self, parser):
        parser.add_argument("--admin-username", default="admin")
        parser.add_argument("--admin-email", default="admin@storepro.vn")
        parser.add_argument(
            "--admin-password",
            default=os.getenv("SEED_ADMIN_PASSWORD", "Admin@123456"),
        )
        parser.add_argument(
            "--staff-password",
            default=os.getenv("SEED_STAFF_PASSWORD", "Staff@123456"),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        store, _ = Store.objects.get_or_create(
            code="STOREPRO",
            defaults={
                "name": "StorePro Shop",
                "phone": "0901 234 567",
                "email": "hello@storepro.vn",
                "address": "Hải Châu, Đà Nẵng",
                "province": "Đà Nẵng",
                "district": "Hải Châu",
            },
        )

        permission_objects = {}
        for code, module, name in PERMISSIONS:
            permission, _ = Permission.objects.get_or_create(
                code=code,
                defaults={"module": module, "name": name},
            )
            permission_objects[code] = permission

        role_permissions = {
            "Admin": list(permission_objects),
            "Quản lý kho": [
                "store.view",
                "warehouse.view",
                "warehouse.manage",
                "product.view",
                "product.create",
                "product.update",
                "inventory.view",
                "inventory.adjust",
                "stockin.create",
                "stockin.view",
                "stockin.complete",
                "stockout.create",
                "stockout.view",
                "stockout.complete",
                "supplier.view",
                "supplier.manage",
                "report.view",
                "notification.view",
            ],
            "Nhân viên bán hàng": [
                "store.view",
                "warehouse.view",
                "product.view",
                "inventory.view",
                "order.view",
                "order.create",
                "order.update",
                "order.cancel",
                "order.complete",
                "customer.view",
                "customer.manage",
                "payment.view",
                "payment.manage",
                "notification.view",
            ],
            "Kế toán": [
                "store.view",
                "order.view",
                "supplier.view",
                "supplier.manage",
                "payment.view",
                "payment.manage",
                "report.view",
                "audit.view",
                "notification.view",
            ],
            "Viewer": [
                "store.view",
                "warehouse.view",
                "product.view",
                "inventory.view",
                "order.view",
                "customer.view",
                "supplier.view",
                "report.view",
                "notification.view",
            ],
        }
        roles = {}
        for role_name, codes in role_permissions.items():
            role, _ = Role.objects.get_or_create(
                store=store,
                name=role_name,
                defaults={"is_system": True},
            )
            role.permissions.set([permission_objects[code] for code in codes])
            roles[role_name] = role

        user, created = User.objects.get_or_create(
            username=options["admin_username"],
            defaults={
                "email": options["admin_email"],
                "first_name": "Nguyễn",
                "last_name": "Văn A",
                "phone": "0901 000 001",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password(options["admin_password"])
            user.save(update_fields=["password"])
        UserProfile.objects.get_or_create(
            user=user,
            defaults={"job_title": "Quản trị viên"},
        )
        membership, _ = StoreMember.objects.get_or_create(
            user=user,
            store=store,
            defaults={"role": roles["Admin"]},
        )

        demo_users = [
            (
                "warehouse",
                "warehouse@storepro.vn",
                "Nguyễn",
                "Quản lý kho",
                "Quản lý kho",
            ),
            (
                "sales",
                "sales@storepro.vn",
                "Trần",
                "Bán hàng",
                "Nhân viên bán hàng",
            ),
            (
                "accountant",
                "accountant@storepro.vn",
                "Lê",
                "Kế toán",
                "Kế toán",
            ),
            (
                "viewer",
                "viewer@storepro.vn",
                "Phạm",
                "Chỉ xem",
                "Viewer",
            ),
        ]
        for username, email, first_name, last_name, role_name in demo_users:
            demo_user, demo_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if demo_created:
                demo_user.set_password(options["staff_password"])
                demo_user.save(update_fields=["password"])
            UserProfile.objects.get_or_create(
                user=demo_user,
                defaults={"job_title": role_name},
            )
            StoreMember.objects.update_or_create(
                user=demo_user,
                store=store,
                defaults={
                    "role": roles[role_name],
                    "status": StoreMember.Status.ACTIVE,
                },
            )

        warehouse, _ = Warehouse.objects.get_or_create(
            store=store,
            code="KHO-DN",
            defaults={
                "name": "Kho chính Đà Nẵng",
                "address": "Hải Châu, Đà Nẵng",
                "province": "Đà Nẵng",
                "district": "Hải Châu",
                "manager": membership,
            },
        )

        categories = {}
        for name in ["Thời trang", "Giày dép", "Phụ kiện"]:
            category, _ = Category.objects.get_or_create(
                store=store,
                slug=slugify(name),
                defaults={"name": name},
            )
            categories[name] = category

        product_data = [
            ("SP001", "Áo thun nam", "Thời trang", "80000", "120000", 50),
            ("SP002", "Quần jean", "Thời trang", "170000", "250000", 8),
            ("SP003", "Giày thể thao", "Giày dép", "520000", "750000", 5),
            ("SP004", "Balo laptop", "Phụ kiện", "240000", "350000", 18),
            ("SP005", "Túi xách", "Phụ kiện", "420000", "650000", 12),
        ]
        for sku, name, category_name, cost, price, quantity in product_data:
            product, _ = Product.objects.get_or_create(
                store=store,
                sku=sku,
                defaults={
                    "category": categories[category_name],
                    "name": name,
                    "slug": slugify(name),
                    "cost_price": Decimal(cost),
                    "selling_price": Decimal(price),
                    "min_stock_level": 10,
                },
            )
            Inventory.objects.get_or_create(
                warehouse=warehouse,
                product=product,
                variant=None,
                defaults={
                    "quantity_on_hand": quantity,
                    "min_stock_level": product.min_stock_level,
                },
            )

        supplier_data = [
            ("NCC001", "Công ty ABC", "0905 123 456"),
            ("NCC002", "NCC XYZ", "0906 222 333"),
            ("NCC003", "Công ty DEF", "0907 333 444"),
        ]
        for code, name, phone in supplier_data:
            Supplier.objects.get_or_create(
                store=store,
                code=code,
                defaults={"name": name, "phone": phone},
            )

        customer_group, _ = CustomerGroup.objects.get_or_create(
            store=store,
            name="Khách hàng thân thiết",
        )
        customer_data = [
            ("KH001", "Nguyễn Văn B", "0901 111 222", "b@gmail.com"),
            ("KH002", "Trần Thị C", "0902 222 333", "c@gmail.com"),
            ("KH003", "Lê Văn D", "0903 333 444", "d@gmail.com"),
        ]
        for code, name, phone, email in customer_data:
            Customer.objects.get_or_create(
                store=store,
                code=code,
                defaults={
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "customer_group": customer_group,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed completed: store, warehouse, roles, admin, products, "
                "suppliers, customers and inventory."
            )
        )
