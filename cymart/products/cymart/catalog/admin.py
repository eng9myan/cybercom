from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name_en", "parent", "is_active", "is_restricted", "display_order"]
    list_filter = ["is_active", "is_restricted", "requires_prescription"]
    prepopulated_fields = {"slug": ("name_en",)}
