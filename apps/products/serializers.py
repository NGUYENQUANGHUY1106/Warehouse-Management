from rest_framework import serializers

from .models import Brand, Category, Product, ProductImage, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

    def validate(self, attrs):
        store = attrs.get("store", getattr(self.instance, "store", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        if store and parent and parent.store_id != store.id:
            raise serializers.ValidationError(
                {"parent": "Danh mục cha phải thuộc cùng gian hàng."}
            )
        return attrs


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "__all__"


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = "__all__"

    def validate(self, attrs):
        store = attrs.get("store", getattr(self.instance, "store", None))
        category = attrs.get(
            "category",
            getattr(self.instance, "category", None),
        )
        brand = attrs.get("brand", getattr(self.instance, "brand", None))
        errors = {}
        if store and category and category.store_id != store.id:
            errors["category"] = "Danh mục phải thuộc cùng gian hàng."
        if store and brand and brand.store_id != store.id:
            errors["brand"] = "Thương hiệu phải thuộc cùng gian hàng."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
