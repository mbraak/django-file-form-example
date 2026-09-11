from django.db import models


class Document(models.Model):
    """A document with a single main file and any number of attachments."""

    title = models.CharField(max_length=200)
    main_file = models.FileField(upload_to="documents/")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title


class Attachment(models.Model):
    document = models.ForeignKey(
        Document, related_name="attachments", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="attachments/")

    def __str__(self):
        return self.file.name
