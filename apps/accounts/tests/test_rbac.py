from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.products.models import Category, Product
from apps.stores.models import Store

from ..models import Permission, Role, StoreMember, User


class AuthenticationAndRBACTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(code="STORE-A", name="Store A")
        self.other_store = Store.objects.create(code="STORE-B", name="Store B")
        self.view_product = Permission.objects.create(
            code="product.view",
            module="product",
            name="View product",
        )
        self.create_product = Permission.objects.create(
            code="product.create",
            module="product",
            name="Create product",
        )
        self.user_view = Permission.objects.create(
            code="user.view",
            module="user",
            name="View user",
        )
        self.role_view = Permission.objects.create(
            code="role.view",
            module="role",
            name="View role",
        )

        self.sales_role = Role.objects.create(store=self.store, name="Sales")
        self.sales_role.permissions.add(self.view_product)
        self.admin_role = Role.objects.create(store=self.store, name="Admin")
        self.admin_role.permissions.add(
            self.view_product,
            self.create_product,
            self.user_view,
            self.role_view,
        )

        self.sales = User.objects.create_user(
            username="sales-test",
            email="sales-test@example.com",
            password="SalesPass123!",
        )
        StoreMember.objects.create(
            user=self.sales,
            store=self.store,
            role=self.sales_role,
        )
        self.admin = User.objects.create_user(
            username="admin-test",
            email="admin-test@example.com",
            password="AdminPass123!",
        )
        StoreMember.objects.create(
            user=self.admin,
            store=self.store,
            role=self.admin_role,
        )

        category = Category.objects.create(
            store=self.store,
            name="Category A",
            slug="category-a",
        )
        other_category = Category.objects.create(
            store=self.other_store,
            name="Category B",
            slug="category-b",
        )
        self.product = Product.objects.create(
            store=self.store,
            category=category,
            sku="SKU-A",
            name="Product A",
            slug="product-a",
            selling_price=Decimal("100"),
        )
        self.other_product = Product.objects.create(
            store=self.other_store,
            category=other_category,
            sku="SKU-B",
            name="Product B",
            slug="product-b",
            selling_price=Decimal("100"),
        )
        self.client = APIClient(HTTP_HOST="localhost")

    def test_html_pages_require_login_and_real_login_creates_session(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

        response = self.client.post(
            "/login/",
            {"identifier": self.sales.email, "password": "SalesPass123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")
        self.assertEqual(
            self.client.session["active_store_id"],
            str(self.store.id),
        )

    def test_sales_can_view_only_products_in_own_store(self):
        self.client.force_authenticate(self.sales)
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(ids, {str(self.product.id)})

    def test_sales_cannot_create_product_or_read_roles(self):
        self.client.force_authenticate(self.sales)
        category = self.product.category
        response = self.client.post(
            "/api/products/",
            {
                "store": str(self.store.id),
                "category": str(category.id),
                "sku": "NEW-SKU",
                "name": "New product",
                "slug": "new-product",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get("/api/roles/").status_code, 403)

    def test_store_admin_cannot_write_to_another_store(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/roles/").status_code, 200)
        response = self.client.post(
            "/api/products/",
            {
                "store": str(self.other_store.id),
                "category": str(self.other_product.category_id),
                "sku": "CROSS-STORE",
                "name": "Cross store product",
                "slug": "cross-store-product",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(sku="CROSS-STORE").exists())

    def test_api_login_returns_role_permissions_and_token(self):
        response = self.client.post(
            "/api/auth/",
            {"username": self.sales.username, "password": "SalesPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["token"])
        self.assertEqual(response.data["role"], "Sales")
        self.assertEqual(response.data["permissions"], ["product.view"])
