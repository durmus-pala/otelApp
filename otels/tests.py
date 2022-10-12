from django.test import TestCase

# Create your tests here.




class OtelFeatures:
    otel = models.ForeignKey(Otel, on_delete=models.CASCADE, verbose_name="Otel")
    feature = models.ForeignKey(OtelFacilityDetail, on_delete=models.CASCADE, verbose_name="Otel Facility Feature")
    isFree = models.BooleanField(default=True, verbose_name="Is Free?")
    created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelfeatures_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelfeatures_update_user')

    class Meta:
        verbose_name = 'Otel Özelliği'
        verbose_name_plural = 'Otel Özellikleri'

    def __str__(self):
        return self.feature.name


class OtelImages:
    otel = models.ForeignKey('otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    otelservice = models.ForeignKey('otels.OtelServiceCategory', on_delete=models.CASCADE,
                                    verbose_name="Otel Service Category")
    video = models.FileField(upload_to='videos/', blank=True, null=True, verbose_name="Video")
    image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name="Image")
    isVideo = models.BooleanField(default=True, verbose_name="Is Video?")
    created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelimages_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelimages_update_user')

    class Meta:
        verbose_name = 'Görsel'
        verbose_name_plural = 'Görseller'

    def __int__(self):
        return self.id
