import pytest
from django.core.exceptions import ValidationError

from products.cymart.catalog.models import Category


@pytest.mark.django_db
class TestCategoryTaxonomy:
    def test_seed_migration_created_top_level_groups(self):
        assert Category.objects.filter(slug="food-and-restaurants", parent__isnull=True).exists()
        assert Category.objects.filter(slug="fashion", parent__isnull=True).exists()
        assert Category.objects.filter(slug="retail", parent__isnull=True).exists()

    def test_unlimited_depth(self):
        root = Category.objects.create(slug="root-x", name_en="Root X")
        a = Category.objects.create(slug="a-x", name_en="A", parent=root)
        b = Category.objects.create(slug="b-x", name_en="B", parent=a)
        c = Category.objects.create(slug="c-x", name_en="C", parent=b)
        d = Category.objects.create(slug="d-x", name_en="D", parent=c)
        assert d.ancestors() == [root, a, b, c]
        assert d.full_path == "Root X / A / B / C / D"

    def test_descendants(self):
        root = Category.objects.create(slug="root-y", name_en="Root Y")
        a = Category.objects.create(slug="a-y", name_en="A", parent=root)
        b = Category.objects.create(slug="b-y", name_en="B", parent=root)
        c = Category.objects.create(slug="c-y", name_en="C", parent=a)
        assert set(root.descendants()) == {a, b, c}

    def test_category_cannot_be_its_own_ancestor(self):
        root = Category.objects.create(slug="root-z", name_en="Root Z")
        child = Category.objects.create(slug="child-z", name_en="Child Z", parent=root)
        root.parent = child
        with pytest.raises(ValidationError):
            root.save()

    def test_restricted_category_from_seed(self):
        medical = Category.objects.get(slug="medical-supplies")
        assert medical.is_restricted is True
        assert medical.restriction_reason != ""

    def test_country_eligibility_default_everywhere(self):
        cat = Category.objects.create(slug="global-cat", name_en="Global")
        assert cat.is_eligible_for_country("JO") is True
        assert cat.is_eligible_for_country("US") is True

    def test_country_eligibility_allow_list(self):
        cat = Category.objects.create(
            slug="jo-only-cat", name_en="Jordan Only", allowed_country_codes=["JO"]
        )
        assert cat.is_eligible_for_country("JO") is True
        assert cat.is_eligible_for_country("US") is False

    def test_healthcare_restriction_fields(self):
        cat = Category.objects.create(
            slug="rx-cat",
            name_en="Prescription Medicine",
            requires_prescription=True,
            is_controlled_substance=True,
            min_age=18,
        )
        assert cat.requires_prescription is True
        assert cat.is_controlled_substance is True
        assert cat.min_age == 18

    def test_bilingual_fields(self):
        cat = Category.objects.create(
            slug="bilingual-cat", name_en="Bakeries", name_ar="مخابز"
        )
        assert cat.name_ar == "مخابز"
