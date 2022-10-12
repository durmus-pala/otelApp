from django.db import models
from django.contrib.auth.models import User


class MyBaseModel(models.Model):
    createdAt = models.DateTimeField(
        auto_now_add=True, verbose_name='created at')
    updatedAt = models.DateTimeField(auto_now=True, verbose_name='updated at')
    createdBy = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='%(app_label)s_%(class)s_created_by')
    updatedBy = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='%(app_label)s_%(class)s_updated_by')
    isDeleted = models.BooleanField(default=False)
    isActive = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Profile(MyBaseModel):
    pass
