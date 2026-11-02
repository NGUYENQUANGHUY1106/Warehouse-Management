import base64
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.accounts.models import Permission, Role, StoreMember, User
from apps.audit_logs.models import AuditLog
from apps.stores.models import Store

from ..models import CatalogStatus, Category, Product, ProductImage, ProductVariant


class ProductCRUDTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(code="PRODUCT-STORE", name="Product Store")
        permissions = {}
        for action in ("view", "create", "update", "delete"):
            code = f"product.{action}"
            permissions[action] = Permission.objects.create(
                code=code,
                module="product",
                name=code,
            )
        admin_role = Role.objects.create(store=self.store, name="Product Admin")
        admin_role.permissions.add(*permissions.values())
        viewer_role = Role.objects.create(store=self.store, name="Product Viewer")
        viewer_role.permissions.add(permissions["view"])
        self.admin = User.objects.create_user(
            username="product-admin",
            email="product-admin@example.com",
            password="AdminPass123!",
        )
        self.viewer = User.objects.create_user(
            username="product-viewer",
            email="product-viewer@example.com",
            password="ViewerPass123!",
        )
        StoreMember.objects.create(user=self.admin, store=self.store, role=admin_role)
        StoreMember.objects.create(user=self.viewer, store=self.store, role=viewer_role)
        self.category = Category.objects.create(
            store=self.store,
            name="Fashion",
            slug="fashion",
        )

    def product_payload(self, **overrides):
        payload = {
            "sku": "WEB-001",
            "barcode": "893000000001",
            "name": "Web Product",
            "slug": "web-product",
            "category": str(self.category.id),
            "brand": "",
            "description": "Created from the real Django form",
            "unit": "cái",
            "cost_price": "100000",
            "selling_price": "150000",
            "min_stock_level": "5",
            "status": CatalogStatus.ACTIVE,
        }
        payload.update(overrides)
        return payload

    def test_real_product_list_reads_database(self):
        product = Product.objects.create(
            store=self.store,
            category=self.category,
            sku="LIST-001",
            name="Database Product",
            slug="database-product",
        )
        self.client.force_login(self.viewer)
        response = self.client.get("/products/?q=Database")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        self.assertContains(response, product.sku)

    def test_create_update_soft_delete_and_restore_product(self):
        self.client.force_login(self.admin)
        response = self.client.post("/products/new/", self.product_payload())
        product = Product.objects.get(sku="WEB-001")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(product.store, self.store)
        self.assertTrue(
            AuditLog.objects.filter(
                module="products",
                action=AuditLog.Action.CREATE,
                object_id=product.id,
            ).exists()
        )

        response = self.client.post(
            f"/products/{product.id}/edit/",
            self.product_payload(name="Updated Product"),
        )
        product.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(product.name, "Updated Product")

        self.client.post(f"/products/{product.id}/delete/")
        product.refresh_from_db()
        self.assertFalse(product.is_active)
        self.assertEqual(product.status, CatalogStatus.ARCHIVED)
        self.assertIsNotNone(product.deleted_at)

        self.client.post(f"/products/{product.id}/restore/")
        product.refresh_from_db()
        self.assertTrue(product.is_active)
        self.assertEqual(product.status, CatalogStatus.ACTIVE)
        self.assertIsNone(product.deleted_at)

    def test_add_variant_and_catalog_category(self):
        product = Product.objects.create(
            store=self.store,
            category=self.category,
            sku="VAR-BASE",
            name="Variant Product",
            slug="variant-product",
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            f"/products/{product.id}/variants/add/",
            {
                "sku": "VAR-S-BLACK",
                "barcode": "",
                "name": "Size S / Black",
                "cost_price": "90000",
                "selling_price": "140000",
                "status": CatalogStatus.ACTIVE,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ProductVariant.objects.filter(product=product, sku="VAR-S-BLACK").exists()
        )

        response = self.client.post(
            "/products/catalog/category/new/",
            {
                "name": "Accessories",
                "slug": "accessories",
                "parent": "",
                "description": "",
                "status": CatalogStatus.ACTIVE,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Category.objects.filter(store=self.store, slug="accessories").exists()
        )

    def test_upload_and_delete_product_image(self):
        product = Product.objects.create(
            store=self.store,
            category=self.category,
            sku="IMAGE-BASE",
            name="Image Product",
            slug="image-product",
        )
        gif = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==")
        self.client.force_login(self.admin)
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    f"/products/{product.id}/images/add/",
                    {
                        "image": SimpleUploadedFile(
                            "product.gif",
                            gif,
                            content_type="image/gif",
                        ),
                        "is_primary": True,
                        "sort_order": 0,
                    },
                )
                self.assertEqual(response.status_code, 302)
                image = ProductImage.objects.get(product=product)
                self.assertTrue(image.is_primary)
                response = self.client.post(
                    f"/products/{product.id}/images/{image.id}/delete/"
                )
                self.assertEqual(response.status_code, 302)
                self.assertFalse(ProductImage.objects.filter(pk=image.id).exists())

    def test_viewer_cannot_open_write_views(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get("/products/").status_code, 200)
        self.assertEqual(self.client.get("/products/new/").status_code, 403)
        self.assertEqual(
            self.client.post("/products/catalog/category/new/", {}).status_code,
            403,
        )

    def test_api_delete_is_soft_delete(self):
        product = Product.objects.create(
            store=self.store,
            category=self.category,
            sku="API-DELETE",
            name="API Delete Product",
            slug="api-delete-product",
        )
        self.client.force_login(self.admin)
        response = self.client.delete(f"/api/products/{product.id}/")
        self.assertEqual(response.status_code, 204)
        product.refresh_from_db()
        self.assertFalse(product.is_active)
        self.assertEqual(product.status, CatalogStatus.ARCHIVED)
