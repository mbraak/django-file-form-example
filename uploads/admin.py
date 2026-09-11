from django.contrib import admin

from .models import Attachment, Document


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "main_file", "created"]
    inlines = [AttachmentInline]
