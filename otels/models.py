from uuid import uuid4
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import os
from django.utils.deconstruct import deconstructible
from django.db.models import JSONField
from django.db.models import signals
import requests
import json
from booking.models import Booking, Collection, Coupon, Customer, CustomerContract, FlightService, Guest, InsuranceService, Invoice, OtelBooking, PriceUpdate, Voucher
from datetime import date
from django.contrib.postgres.fields import ArrayField
iller = {"adana": "01",
         "adıyaman": "02",
         "aksaray": "68",
         "ardahan": "75",
         "afyonkarahisar": "03",
         "ağrı": "04",
         "amasya": "05",
         "ankara": "06",
         "antalya": "07",
         "artvin": "08",
         "aydın": "09",
         "balıkesir": "10",
         "bartın": "74",
         "batman": "72",
         "bayburt": "69",
         "bilecik": "11",
         "bingöl": "12",
         "bitlis": "13",
         "bolu": "14",
         "burdur": "15",
         "bursa": "16",
         "çanakkale": "17",
         "çankırı": "18",
         "çorum": "19",
         "denizli": "20",
         "diyarbakır": "21",
         "düzce": "81",
         "edirne": "22",
         "elazığ": "23",
         "erzincan": "24",
         "erzurum": "25",
         "eskişehir": "26",
         "gaziantep": "27",
         "giresun": "28",
         "gümüşhane": "29",
         "hakkari": "30",
         "hatay": "31",
         "ığdır": "76",
         "ısparta": "32",
         "mersin": "33",
         "istanbul": "34",
         "izmir": "35",
         "karabük": "78",
         "karaman": "70",
         "kars": "36",
         "kastamonu": "37",
         "kayseri": "38",
         "kırıkkale": "71",
         "kırklareli": "39",
         "kırşehir": "40",
         "kilis": "79",
         "kocaeli": "41",
         "konya": "42",
         "kütahya": "43",
         "malatya": "44",
         "manisa": "45",
         "kahramanmaraş": "46",
         "mardin": "47",
         "muğla": "48",
         "muş": "49",
         "nevşehir": "50",
         "niğde": "51",
         "ordu": "52",
         "osmaniye": "80",
         "rize": "53",
         "sakarya": "54",
         "samsun": "55",
         "siirt": "56",
         "sinop": "57",
         "sivas": "58",
         "şırnak": "73",
         "tekirdağ": "59",
         "tokat": "60",
         "trabzon": "61",
         "tunceli": "62",
         "şanlıurfa": "63",
         "uşak": "64",
         "van": "65",
         "yalova": "77",
         "yozgat": "66",
         "zonguldak": "67"
         }


@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        # add extension as per your requirement, I am using .png
        # print(filename)
        import os
        fname, fext = os.path.splitext(filename)
        if not fext:
            ext = "png"
        # set filename as random string
        filename = '{}-{}-{}.{}'.format(instance.otel.name,
                                        instance.imageCategory.name, uuid4().hex, fext)
        # filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)


def generate_unique_slug(klass, field):
    """
    return unique slug if origin slug is exist.
    eg: `foo-bar` => `foo-bar-1`

    :param `klass` is Class model.
    :param `field` is specific field for title.
    """
    origin_slug = slugify(field)
    unique_slug = origin_slug
    numb = 1
    while klass.objects.filter(slug=unique_slug).exists():
        unique_slug = '%s-%d' % (origin_slug, numb)
        numb += 1
    return unique_slug


def photo_path(instance, filename):
    import os
    file_extension = os.path.splitext(filename)
    return 'logos/{otelname}{ext}'.format(otelname=instance.name, ext=file_extension)


def path_and_rename(instance, filename, content_type):
    import os
    # upload_to =
    ext = filename.split('.')[-1]
    # get filename

    if instance.pk:
        filename = '{}/{}-{}-{}.{}'.format(content_type, instance.otel.name, instance.otelservice.name, uuid4().hex,
                                           ext)
    else:
        # set filename as random string
        filename = '{}/{}-{}-{}.{}'.format(content_type, instance.otel.name, instance.otelservice.name, uuid4().hex,
                                           ext)
        # filename = '{}-{}-{}.{}'.format(instance.otel.name, instance.otelservice.name,uuid4().hex, ext)
        # filename = '{}.{}'.format(uuid4().hex, ext)
    # return the whole path to the file
    return os.path.join('uploads', filename)


# Create your models here.

class OtelChain(models.Model):
    name = models.CharField(max_length=30, verbose_name="Name", blank=True)
    website = models.CharField(
        max_length=50, verbose_name="Web Site", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelchain_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelchain_update_user')

    class Meta:
        verbose_name = 'Otel Zinciri'
        verbose_name_plural = 'Otel Zinciri'

    def __str__(self):
        return self.name


class Airport(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name", blank=True)
    code = models.CharField(
        max_length=3, verbose_name="Airport Code XYZ", blank=True)
    country = models.ForeignKey('cities_light.Country', on_delete=models.DO_NOTHING, verbose_name="Ülke", blank=True,
                                null=True)
    region = models.ForeignKey('cities_light.Region', on_delete=models.DO_NOTHING, verbose_name="İl", blank=True,
                               null=True)
    subRegion = models.ForeignKey('cities_light.SubRegion', on_delete=models.DO_NOTHING, verbose_name="İlçe",
                                  blank=True, null=True)
    location = models.ForeignKey('cities_light.City', on_delete=models.DO_NOTHING, verbose_name="Mevki", blank=True,
                                 null=True)
    # location  = models.CharField(max_length=50, verbose_name="Mevki", blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    isActive = models.BooleanField(
        default=True, verbose_name="Is Active", blank=True, null=True)
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='airport_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='airport_update_user')

    class Meta:
        verbose_name = 'Hava Alanı'
        verbose_name_plural = 'Hava Alanları'

    def __str__(self):
        return self.name


class OtelCategory(models.Model):
    name = models.CharField(
        max_length=100, verbose_name="Name", blank=True, null=True)
    name_en = models.CharField(
        max_length=100, verbose_name="Name En", blank=True, null=True)
    name_ru = models.CharField(
        max_length=100, verbose_name="Name Ru", blank=True, null=True)
    isMain = models.BooleanField(
        default=True, verbose_name="Is Main Category?")
    upCategory = models.ManyToManyField("self", blank=True)
    color = models.CharField(max_length=7, verbose_name="Color", blank=True)
    isOtel = models.BooleanField(default=True, verbose_name="Is Otel?")
    isTour = models.BooleanField(default=False, verbose_name="Is Tour?")
    isTransfer = models.BooleanField(
        default=False, verbose_name="Is Transfer?")
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelcategory_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelcategory_update_user')

    class Meta:
        verbose_name = 'Otel Kategorisi'
        verbose_name_plural = 'Otel Kategorileri'

    def __str__(self):
        return self.name


class OtelTheme(models.Model):
    name = models.CharField(
        max_length=100, verbose_name="Name", blank=True, null=True)
    name_en = models.CharField(
        max_length=100, verbose_name="Name En", blank=True, null=True)
    name_ru = models.CharField(
        max_length=100, verbose_name="Name Ru", blank=True, null=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='oteltheme_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='oteltheme_update_user')

    class Meta:
        verbose_name = 'Otel Teması'
        verbose_name_plural = 'Otel Temaları'

    def __str__(self):
        return self.name


class UploadFile(models.Model):
    file = models.FileField(upload_to='allFiles/',
                            max_length=255, null=True, blank=True)
    isActive = models.BooleanField(default=True)

    class Meta:
        db_table = 'uploadfile'
        verbose_name = 'uploadfile'
        verbose_name_plural = 'uploadfiles'

    def __str__(self):
        return str(self.id)


class Contract(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")

    contractPerson = models.CharField(
        max_length=30, verbose_name="Conctract Person", blank=True)
    description = models.CharField(
        max_length=250, verbose_name="Contract Description", blank=True)
    startDate = models.DateField(
        verbose_name="Start Date", blank=True, null=True)
    finishDate = models.DateField(
        verbose_name="Finish Date", blank=True, null=True)
    contractAccomodationStartDate = models.DateField(
        verbose_name="contractAccomodationStartDate", blank=True, null=True)
    contractAccomodationEndDate = models.DateField(
        verbose_name="contractAccomodationEndDate", blank=True, null=True)
    files = ArrayField(models.CharField(
        max_length=255), null=True, blank=True)
    isPurchasePrice = models.BooleanField(
        default=False, verbose_name="Is Purchase Price or Sale Price?")
    isHaveContract = models.BooleanField(
        default=False, verbose_name="Is Have a Contract?")
    isOverride = models.BooleanField(
        default=False, verbose_name="Is Override?")
    isContractActive = models.BooleanField(
        default=True, verbose_name="Is Contrat Active?")
    isStaus = models.BooleanField(
        default=False, verbose_name="Is Status?")
    customerPaymentType = models.ManyToManyField('otels.CustomerPaymentType', verbose_name="Customer Payment Type",
                                                 blank=True)
    otelContractPaymentType = models.ManyToManyField('otels.OtelContractPaymentType',
                                                     verbose_name="Otel Contract Payment Type", blank=True)
    inDays = models.ManyToManyField(
        'accomodations.inDays', verbose_name="Days", blank=True)
    minPayment = models.IntegerField(
        verbose_name="Percentage of Minimum Payment", blank=True, null=True, default=10)
    contractType = models.CharField(
        max_length=250, verbose_name="Conctract Type", blank=True)
    contractShape = models.CharField(
        max_length=250, verbose_name="Conctract Shape", blank=True)
    paymentAmount = models.FloatField(null=True, blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active?")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='contract_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='contract_update_user')

    class Meta:
        verbose_name = 'Kontrat'
        verbose_name_plural = 'Kontratlar'

    def __str__(self):
        return "{} - {}".format(self.id, self.otel.name)


class PaymentMethod(models.Model):
    # PAYMENT_METHODS = [
    #     (1, 'Nakit'),
    #     (2, 'Kredi Karti'),
    #     (3, 'Banki Karti'),
    #     (4, 'Çek'),
    #     (5, 'Diger'),
    # ]
    name = models.CharField(
        max_length=30, verbose_name="Payment Method Name", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active?")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='paymentmethod_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='paymentmethod_update_user')

    class Meta:
        verbose_name = 'Ödeme YÖntemi'
        verbose_name_plural = 'Ödeme Yöntemleri'

    def __str__(self):
        return self.name


class PayAtFacility(models.Model):
    contract = models.ForeignKey('otels.Contract', on_delete=models.CASCADE, verbose_name="Contract",
                                 related_name='payatfacilitychoices')
    roomType = models.ManyToManyField(
        'accomodations.RoomType', verbose_name="RoomTypes", blank=True)
    startDate = models.DateField(
        verbose_name="Start Date", blank=True, null=True)
    finishDate = models.DateField(
        verbose_name="Finish Date", blank=True, null=True)
    inDays = models.ManyToManyField(
        'accomodations.inDays', verbose_name="Days", blank=True)
    minDays = models.IntegerField(
        verbose_name="Min Days", blank=True, null=True)
    maxDays = models.IntegerField(
        verbose_name="Max Days", blank=True, null=True)
    paymentPercentage = models.IntegerField(
        verbose_name="Percentage of Payment", blank=True, null=True)
    # paymentMethod = models.ManyToManyField('otels.PaymentMethod', verbose_name="PaymentMethod", blank=True)
    # paymentMethod = models.IntegerField(blank=True, null=True, default=1, choices=PAYMENT_METHODS)
    isActive = models.BooleanField(default=True, verbose_name="Is Active?")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='payatfacility_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='payatfacility_update_user')

    class Meta:
        verbose_name = 'Tesiste Ödeme Seçeneği'
        verbose_name_plural = 'Tesiste Ödeme Seçenekleri'

    def __str__(self):
        return str(self.id)


class PaymentPlan(models.Model):
    PAYMENT_PLANS = [
        (1, 'Belirtilen Tarihte'),
        (2, 'Rezervasyon Tarihinden Önce'),
        (3, 'Rezervasyon Tarihinden Sonra'),
        (4, 'Check in Tarihinden Önce'),
        (5, 'Check in Tarihinden Sonra'),
        (6, 'Check out Tarihinden Önce'),
        (7, 'Check out Tarihinden Sonra'),
    ]

    contract = models.ForeignKey('otels.Contract', on_delete=models.CASCADE, verbose_name="Contract",
                                 related_name='patmentplans')
    paymentplan = models.IntegerField(
        blank=True, null=True, default=1, choices=PAYMENT_PLANS)
    day = models.IntegerField(verbose_name="Day", blank=True, null=True)
    date = models.DateField(verbose_name="Date", blank=True, null=True)
    paymentPercentage = models.IntegerField(
        verbose_name="Percentage of Payment", blank=True, null=True)
    description = models.CharField(
        max_length=250, verbose_name="Payment Description", blank=True)
    # 'Belirtilen Tarihte'
    isPaymentByCheck = models.BooleanField(
        default=False, verbose_name="Is Payment Accepted by Check?")
    isPaymentByCreditCard = models.BooleanField(
        default=False, verbose_name="Is Payment Accepted by CreditCard?")
    isPaymentByMoneyTransfer = models.BooleanField(
        default=False, verbose_name="Is Payment Accepted by MoneyTransfer?")
    checkIssueDate = models.DateField(
        verbose_name="check Issue Date", blank=True, null=True)
    checkPaymentDate = models.DateField(
        verbose_name="check Payment Date", blank=True, null=True)
    checkPaymentAmount = models.FloatField(
        verbose_name="check Payment Amount", blank=True, null=True)
    checkDescription = models.CharField(
        max_length=250, verbose_name="check Description", blank=True)
    # paymentMethod = models.ManyToManyField('otels.PaymentMethod', verbose_name="PaymentMethod", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active?")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='paymentplan_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='paymentplan_update_user')

    class Meta:
        verbose_name = 'Ödeme Planı'
        verbose_name_plural = 'Ödeme Planları'

    def __str__(self):
        return str(self.id)


class StakeHolderContact(models.Model):
    fullName = models.CharField(
        max_length=100, verbose_name="Name", blank=True)
    personposition = models.ForeignKey('management.OtelPersonPosition', null=True, blank=True,
                                       on_delete=models.DO_NOTHING, verbose_name="OtelPersonPosition")
    title = models.CharField(max_length=50, verbose_name="Title", blank=True)
    phone = models.CharField(
        max_length=20, verbose_name="Phone", null=True, blank=True)
    email = models.EmailField(verbose_name="Email", blank=True)
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='stakeholder_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='stakeholder_update_user')

    class Meta:
        verbose_name = 'Otel Yetkili Bilgisi'
        verbose_name_plural = 'Yetkili Bilgileri'

    def __str__(self):
        return self.fullName


class Supplier(models.Model):
    title = models.CharField(
        max_length=50, verbose_name="Supplier Title", blank=True, null=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='supplier_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='supplier_update_user')

    class Meta:
        verbose_name = 'Tedarikçi'
        verbose_name_plural = 'Tedarikçiler'

    def __str__(self):
        return self.title


class OtelType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='oteltype_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='oteltype_update_user')

    class Meta:
        verbose_name = 'Otel Tipi'
        verbose_name_plural = 'Otel Tipleri'

    def __str__(self):
        return self.name


class Otel(models.Model):
    name = models.CharField(max_length=150, null=True,
                            blank=True, verbose_name="Name")
    otelLogo = models.CharField(max_length=255, null=True, blank=True)
    erpNo = models.CharField(
        max_length=20, verbose_name="ERP No", blank=True, null=True)
    description = models.CharField(
        max_length=250, verbose_name="Description", null=True, blank=True)
    operationNote = models.TextField(
        verbose_name="Operation Note", blank=True, null=True)
    address = models.CharField(
        max_length=250, verbose_name="Address", blank=True, null=True)
    email = models.TextField(verbose_name="Email", blank=True, null=True)
    seoText = models.TextField(verbose_name="Seo Text", blank=True, null=True)
    supplier = models.ManyToManyField(
        'otels.Supplier', verbose_name="Supplier", null=True, blank=True)
    supplierNotes = models.TextField(
        verbose_name="Supplier Notes", blank=True, null=True)
    category = models.ManyToManyField(
        OtelCategory, verbose_name="Categories", blank=True, null=True)
    theme = models.ManyToManyField(
        OtelTheme, verbose_name="Themes", blank=True, null=True)
    airport = models.ManyToManyField(
        Airport, verbose_name="Airports", blank=True, null=True)
    salesChannel = models.ManyToManyField(
        'actions.SalesChannel', verbose_name="Sales Channel", null=True, blank=True)
    phone1 = models.CharField(
        max_length=20, verbose_name="Phone 1", blank=True, null=True)
    phone2 = models.CharField(
        max_length=20, verbose_name="Phone 2", blank=True, null=True)
    priceStatus = models.BooleanField(default=False)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    isReklamStatus = models.BooleanField(
        default=True, verbose_name="isReklamStatus")
    isStatusActive = models.BooleanField(
        default=True, verbose_name="Is Otel Active")
    otelChain = models.ForeignKey(OtelChain, on_delete=models.DO_NOTHING, verbose_name="Otel Chain",
                                  blank=True, null=True)
    otelType = models.ForeignKey('otels.OtelType', on_delete=models.DO_NOTHING, verbose_name="Otel Tipi", blank=True,
                                 null=True)
    country = models.ForeignKey('cities_light.Country', on_delete=models.DO_NOTHING, verbose_name="Ülke", blank=True,
                                null=True)
    region = models.ForeignKey('cities_light.Region', on_delete=models.DO_NOTHING, verbose_name="İl", blank=True,
                               null=True)
    subRegion = models.ForeignKey('cities_light.SubRegion', on_delete=models.DO_NOTHING, verbose_name="İlçe",
                                  blank=True, null=True)
    location = models.ForeignKey('cities_light.City', on_delete=models.DO_NOTHING, verbose_name="Mevki", blank=True,
                                 null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    distancesToPOIS = JSONField(null=True, blank=True)
    extraFeatures = JSONField(null=True, blank=True)
    otelManagerData = JSONField(null=True, blank=True)

    # fields needed for netsis integration
    ytLink = models.URLField(
        max_length=250, verbose_name="Youtube link", blank=True, null=True)
    taxOffice = models.CharField(
        max_length=250, verbose_name="Tax Office", blank=True, null=True, default="")
    taxNumber = models.CharField(
        max_length=250, verbose_name="Tax Number", blank=True, null=True, default="")
    postalCode = models.CharField(
        max_length=250, verbose_name="Postal Code", blank=True, null=True)
    isDelivered = models.BooleanField(
        default=False, verbose_name="is Delivered to Netsis")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otel_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otel_update_user')
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        verbose_name = 'Otel'
        verbose_name_plural = 'Oteller'

    def save(self, *args, **kwargs):
        if self.slug:  # edit
            if slugify(self.name) != self.slug:
                self.slug = generate_unique_slug(Otel, self.name)
        else:  # create
            self.slug = generate_unique_slug(Otel, self.name)

        super(Otel, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.id)


def update_otel_status(sender, instance, created, **kwargs):
    if instance.isActive == False:
        from accomodations.models import Accomodation, PriceDetails, Quota, RoomType
        from actions.models import ActionPriceDetail, MainAction
        OtelImages.objects.filter(otel__id=instance.id).update(isActive=False)
        RoomType.objects.filter(otel__id=instance.id).update(isActive=False)
        Quota.objects.filter(otel__id=instance.id).update(isActive=False)
        Contract.objects.filter(otel__id=instance.id).update(isActive=False)
        PriceDetails.objects.filter(
            otel__id=instance.id).update(isActive=False)
        Accomodation.objects.filter(
            otel__id=instance.id).update(isActive=False)
        MainAction.objects.filter(otel__id=instance.id).update(isActive=False)
        ActionPriceDetail.objects.filter(
            action__otel__id=instance.id).update(isActive=False)


signals.post_save.connect(update_otel_status, sender=Otel)


class OtelServiceCategory(models.Model):
    name = models.CharField(
        max_length=100, verbose_name="Name", blank=True, null=True)
    name_en = models.CharField(
        max_length=100, verbose_name="Name En", blank=True, null=True)
    name_ru = models.CharField(
        max_length=100, verbose_name="Name Ru", blank=True, null=True)

    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelservicevategory_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelservicevategory_update_user')

    class Meta:
        verbose_name = 'Otel Servis Kategorisi'
        verbose_name_plural = 'Otel Servis Kategorileri'

    def __str__(self):
        return self.name


class OtelFacilityDetail(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name", blank=True)
    name_en = models.CharField(
        max_length=100, verbose_name="Name En", blank=True, null=True)
    name_ru = models.CharField(
        max_length=100, verbose_name="Name Ru", blank=True, null=True)
    serviceCategory = models.ForeignKey(
        OtelServiceCategory, on_delete=models.CASCADE, verbose_name="Service Category")
    feature = models.TextField(verbose_name="Feature", blank=True)
    feature_en = models.TextField(
        verbose_name="Feature En", blank=True, null=True)
    feature_ru = models.TextField(
        verbose_name="Feature Ru", blank=True, null=True)
    iconClassName = models.CharField(
        max_length=100, verbose_name="Icon Class Name", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    isPrice = models.BooleanField(
        default=False, verbose_name="Is Price", blank=True)
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelfacilitydetail_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelfacilitydetail_update_user')

    class Meta:
        verbose_name = 'Otel Tesis Detayı'
        verbose_name_plural = 'Otel Tesis Detayları'

    def __str__(self):
        return self.name


class OtelFeatures(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    feature = models.ForeignKey(
        OtelFacilityDetail, on_delete=models.CASCADE, verbose_name="Otel Facility Feature")
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelfeatures_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelfeatures_update_user')

    class Meta:
        verbose_name = 'Otel Özelliği'
        verbose_name_plural = 'Otel Özellikleri'

    def __str__(self):
        return self.feature.name


class OtelImages(models.Model):
    PROCESS_TYPES = [
        (1, 'Yeni Kayıt'),
        (2, 'Güncelleme'),
        (3, 'Varsayılan Atama'),
        (4, 'Silme'),
    ]
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    imageCategory = models.ForeignKey('otels.OtelServiceCategory', on_delete=models.CASCADE,
                                      verbose_name="Image Category", null=True, blank=True)
    roomType = models.ForeignKey('accomodations.RoomType', verbose_name="RoomTypes", blank=True, null=True,
                                 on_delete=models.CASCADE)
    title = models.CharField(max_length=35, verbose_name="Title", blank=True)
    description = models.CharField(
        max_length=250, verbose_name="Description", blank=True)

    file = models.FileField(upload_to='upload/', null=True,
                            blank=True, verbose_name="Video")
    processType = models.IntegerField(
        blank=True, null=True, default=1, choices=PROCESS_TYPES)
    isVideo = models.BooleanField(default=True, verbose_name="Is Video?")

    imageOrder = models.IntegerField(blank=True, null=True)
    isDefault = models.BooleanField(default=False, verbose_name="Is Default?")
    isPrimary = models.BooleanField(default=False, verbose_name="Is Primary?")

    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelimages_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelimages_update_user')

    class Meta:
        verbose_name = 'Görsel'
        verbose_name_plural = 'Görseller'

    def __int__(self):
        return self.id

    def save(self, *args, **kwargs):
        if self.imageCategory.id == 2:
            if self.isDefault == True:
                OtelImages.objects.filter(
                    otel__id=self.otel.id, roomType__id=self.roomType.id, isDefault=True).update(isDefault=False)
        else:
            if self.isDefault == True:
                OtelImages.objects.filter(
                    otel__id=self.otel.id, roomType__id=None, isDefault=True).update(isDefault=False)
        super(OtelImages, self).save(*args, **kwargs)


def delete_otel_image(sender, instance=None, **kwargs):
    imageOrders = OtelImages.objects.filter(imageOrder__gt=instance.imageOrder)
    for eachImageOrder in imageOrders:
        eachImageOrder.imageOrder -= 1
        eachImageOrder.save()


signals.post_delete.connect(delete_otel_image, sender=OtelImages)


class CustomerPaymentType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='customerpaymentcategory_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='customerpaymentcategory_update_user')

    class Meta:
        verbose_name = 'Musteri Ödeme Aksiyonu'
        verbose_name_plural = 'Musteri Ödeme Aksiyonları'

    def __str__(self):
        return self.name


class OtelContractPaymentType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelcontractpaymenttype_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelcontractpaymenttype_update_user')

    class Meta:
        verbose_name = 'Otel Ödeme Aksiyonu'
        verbose_name_plural = 'Otel Ödeme Aksiyonları'

    def __str__(self):
        return self.name


class OtelServiceDescription(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    serviceCategory = models.ForeignKey('otels.OtelServiceCategory', on_delete=models.CASCADE,
                                        verbose_name="OtelServiceCategory")
    startDate = models.DateField(
        verbose_name="Start Date", blank=True, null=True)
    finishDate = models.DateField(
        verbose_name="Finish Date", blank=True, null=True)
    descscription = models.TextField(
        verbose_name="Description", blank=True, null=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelservicedescription_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelservicedescription_update_user')

    class Meta:
        verbose_name = 'Otel Servisleri Açıklamasi'
        verbose_name_plural = 'Otel Servisleri Açıklamaları'

    def __int__(self):
        return self.id


class PeriodicDescriptionType(models.Model):
    """
        bu kisida (freeActivity, paidActivity, honeymoon, covid19,notes) kategorileri eklenecek
    """
    name = models.CharField(max_length=100, verbose_name="Name", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='periodicdescriptiontype_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='periodicdescriptiontype_update_user')

    class Meta:
        verbose_name = 'Dönemsel Açıklama Tipi'
        verbose_name_plural = 'Dönemsel Açıklama Tipleri'

    def __str__(self):
        return self.name


class PeriodicDescription(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    startDate = models.DateField(
        verbose_name="Start Date", blank=True, null=True)
    finishDate = models.DateField(
        verbose_name="Finish Date", blank=True, null=True)
    title = models.CharField(max_length=255, verbose_name="Title", blank=True)
    descriptionType = models.ForeignKey('otels.PeriodicDescriptionType', on_delete=models.CASCADE,
                                        verbose_name="PeriodicDescription", blank=True, default=2)
    description = models.TextField(verbose_name="Description", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='periodicdescription_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='periodicdescription_update_user')

    class Meta:
        verbose_name = 'Dönemsel Açıklama'
        verbose_name_plural = 'Dönemsel Açıklamalar'

    def __int__(self):
        return self.id


class PensionTypePeriodicDescription(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    pensionType = models.ForeignKey('accomodations.PensionType', on_delete=models.DO_NOTHING,
                                    verbose_name="Pansiyon Tipi", blank=True)
    startDate = models.DateField(
        verbose_name="Start Date", blank=True, null=True)
    finishDate = models.DateField(
        verbose_name="Finish Date", blank=True, null=True)
    title = models.CharField(max_length=250, verbose_name="Title", blank=True)
    description = models.CharField(
        max_length=250, verbose_name="Description", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='roomtypeperiodicdescription_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='roomtypeperiodicdescription_update_user')

    class Meta:
        verbose_name = 'Pansiyontipi Dönemsel Açıklama'
        verbose_name_plural = 'Pansiyontipi Dönemsel Açıklamalar'

    def __int__(self):
        return self.id


class OtelOwnership(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    owners = models.ManyToManyField(User, verbose_name="Owner of otel",
                                    related_name='owner_user')

    # owners = models.ManyToManyField(User, default=1, verbose_name="Owners", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='otelownership_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='otelownership_update_user')

    class Meta:
        verbose_name = 'Otel sahibi'
        verbose_name_plural = 'Otel sahipleri'

    def __int__(self):
        return self.id


class ModuleFormFeatures(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel")
    orientation = models.CharField(
        max_length=250, verbose_name="Dikey/Yatay Yonlendirme", blank=True)
    position = models.CharField(
        max_length=250, verbose_name="Sag/sol/orta", blank=True)
    themeColor = models.CharField(
        max_length=250, verbose_name="Tema Rengi", blank=True)
    bgColor = models.CharField(
        max_length=250, verbose_name="BG renk", blank=True)
    subTitleColor = models.CharField(
        max_length=250, verbose_name="SubTitle renk", blank=True)
    resBtnColor = models.CharField(
        max_length=250, verbose_name="resBtnColor", blank=True)
    callBtnColor = models.CharField(
        max_length=250, verbose_name="callBtnColor", blank=True)
    transparency = models.FloatField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    # isGroupHotel = models.BooleanField(default=False, verbose_name="Is Group Hotel")
    # isSubtitleActive = models.BooleanField(default=True, verbose_name="Is Subtitle Active")
    isGroupHotel = models.CharField(
        max_length=250, verbose_name="is Group Hotel", blank=True)
    isSubtitleActive = models.CharField(
        max_length=250, verbose_name="is Subtitle Active", blank=True)
    subtitleText = models.CharField(
        max_length=250, verbose_name="Subtitle Text", blank=True)
    # isPaymentSystem = models.BooleanField(default=True, verbose_name="Is Payment System")
    isPaymentSystem = models.CharField(
        max_length=250, verbose_name="is Payment System", blank=True)
    phoneNumber = models.CharField(
        max_length=250, verbose_name="phoneNumber", blank=True)
    fontColor = models.CharField(
        max_length=250, verbose_name="fontColor", blank=True)
    isMobileFooter = models.BooleanField(
        default=True, verbose_name="isMobileFooter")
    isChatbot = models.BooleanField(default=True, verbose_name="isChatbot")
    isPushNotif = models.BooleanField(default=True, verbose_name="isPushNotif")
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='moduleformfeature_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='moduleformfeature_update_user')

    class Meta:
        verbose_name = 'Modul Form Ozelligi'
        verbose_name_plural = 'Modul Form Ozellikleri'

    def __int__(self):
        return self.id


class Bank(models.Model):
    name = models.CharField(
        max_length=250, verbose_name="Bank name", blank=True)
    logoImage = models.ImageField(
        upload_to='images/', blank=True, null=True, verbose_name="Image")
    # logo /= models.ImageField(upload_to=PathAndRename('logos/'), blank=True, null=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='bank_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='bank_update_user')

    class Meta:
        verbose_name = 'Banka'
        verbose_name_plural = 'Bankalar'

    def __str__(self):
        return self.name


class PaymentAccountInfo(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel", null=True, blank=True)
    bank = models.ForeignKey(
        'otels.Bank', on_delete=models.CASCADE, verbose_name="Bank", null=True, blank=True)
    note = models.CharField(
        max_length=250, verbose_name="Aciklamalar", null=True, blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='paymentaccountinfo_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='paymentaccountinfo_update_user')

    class Meta:
        verbose_name = 'Modul Odeme Bilgisi'
        verbose_name_plural = 'Modul Odeme Bilgileri'

    def __int__(self):
        return self.id


class ChilConditionTheme(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel", null=True, blank=True)
    childCondition = models.ForeignKey(
        'accomodations.ChildCondition', on_delete=models.CASCADE, verbose_name="ChildCondition", null=True, blank=True)
    name = models.CharField(
        max_length=250, verbose_name="Name", null=True, blank=True)
    ratio = models.FloatField(
        max_length=250, verbose_name="Ratio", null=True, blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='chilconditiontheme_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='chilconditiontheme_update_user')

    class Meta:
        verbose_name = 'Çocuk Şartı Teması'
        verbose_name_plural = 'Çocuk Şartı Temaları'

    def __int__(self):
        return self.id


class AccountInfo(models.Model):
    otel = models.ForeignKey(
        'otels.Otel', on_delete=models.CASCADE, verbose_name="Otel", blank=True, null=True)
    bank = models.ForeignKey(
        'otels.Bank', on_delete=models.CASCADE, verbose_name="Bank")
    iban = models.CharField(max_length=250, verbose_name="IBAN", blank=True)

    accountType = models.CharField(
        max_length=250, verbose_name="Hesap Turu", blank=True)
    swiftcode = models.CharField(
        max_length=250, verbose_name="swift kodu", blank=True)
    accountNo = models.CharField(
        max_length=250, verbose_name="account no", blank=True)
    branchNo = models.CharField(
        max_length=250, verbose_name="sube no", blank=True)

    branch = models.CharField(max_length=250, verbose_name="Sube", blank=True)
    commissionRate = models.FloatField(blank=True, null=True, default=0)
    currencyType = models.ForeignKey('accomodations.Currency', on_delete=models.DO_NOTHING, verbose_name="currency type",
                                     blank=True, null=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    isStatusActive = models.BooleanField(
        default=True, verbose_name="Is Status Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='accountinfo_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='accountinfo_update_user')

    class Meta:
        verbose_name = 'Banka Hesabı'
        verbose_name_plural = 'Banka Hesapları'

    def __str__(self):
        return self.bank.name


class HotelGroup(models.Model):
    groupName = models.CharField(
        max_length=250, verbose_name="Otel Groupname", blank=True, null=True)
    otel = models.ManyToManyField(
        'otels.Otel', verbose_name="Otel", blank=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='hotelgroup_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='hotelgroup_update_user')

    class Meta:
        verbose_name = 'Otel Grubu'
        verbose_name_plural = 'Otel Grupları'

    def __str__(self):
        if self.groupName == None:
            return "No name"
        return self.groupName


class EpidemicMeasures(models.Model):
    otel = models.ForeignKey('otels.Otel', verbose_name="Otel", related_name='epidemicmeasure',
                             on_delete=models.DO_NOTHING, blank=True, null=True)
    measuresJSON = JSONField(null=True, blank=True,
                             verbose_name="Epidemic Measures Json")
    # measuresJSON = JSONField(null=True, blank=True, verbose_name="Epidemic Measures Json", default=epidemicMeasureDefault)
    otherMeasures = models.TextField(
        verbose_name="Other Measures", blank=True, null=True)
    certificate = models.FileField(upload_to='certificate/', blank=True,
                                   null=True, verbose_name="Koronavirüs Önlemleri Bakanlık Sertifikası")
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='epidemicmeasures_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='epidemicmeasures_update_user')

    class Meta:
        verbose_name = 'Salgın Hastalık Tedbiri'
        verbose_name_plural = 'Salgın Hastalık Tedbirleri'

    def __int__(self):
        return self.id


class InvoiceInfo(models.Model):
    otel = models.ForeignKey('otels.Otel', verbose_name="Otel", related_name='invoiceinfo',
                             on_delete=models.DO_NOTHING, blank=True, null=True)
    region = models.ForeignKey('cities_light.Region', on_delete=models.DO_NOTHING, verbose_name="İl", blank=True,
                               null=True)
    subRegion = models.ForeignKey('cities_light.SubRegion', on_delete=models.DO_NOTHING, verbose_name="İlçe",
                                  blank=True, null=True)
    postalCode = models.CharField(
        max_length=100, verbose_name="Posta kodu", blank=True, null=True)
    address = models.CharField(
        max_length=250, verbose_name="Adres", blank=True, null=True)
    title = models.CharField(
        max_length=250, verbose_name="Ticari Unvan", blank=True, null=True)
    taxOffice = models.CharField(
        max_length=250, verbose_name="Vergi dairesi", blank=True, null=True)
    taxNumber = models.CharField(
        max_length=250, verbose_name="Vergi numarasi", blank=True, null=True)
    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='invoiceinfo_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='invoiceinfo_update_user')

    class Meta:
        verbose_name = 'Fatura Bilgisi'
        verbose_name_plural = 'Fatura Bilgileri'

    def __int__(self):
        return self.id


class ContractItemsApproval(models.Model):
    otel = models.ForeignKey('otels.Otel', verbose_name="Otel", related_name='contractitems',
                             on_delete=models.DO_NOTHING, blank=True, null=True)

    item1 = models.BooleanField(default=False, verbose_name="Item 1")
    item2 = models.BooleanField(default=False, verbose_name="Item 2")
    item3 = models.BooleanField(default=False, verbose_name="Item 3")

    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='contractitemsapproval_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='contractitemsapproval_update_user')

    class Meta:
        verbose_name = 'Sözleşme Şartı'
        verbose_name_plural = 'Sözleşme Şartları'

    def __int__(self):
        return self.id


class CCInterestRatio(models.Model):
    otel = models.ForeignKey('otels.Otel', verbose_name="Otel",
                             on_delete=models.DO_NOTHING, blank=True, null=True)
    bank = models.ForeignKey('otels.Bank', verbose_name="Bank",
                             on_delete=models.DO_NOTHING, blank=True, null=True)
    interestRatios = JSONField(
        null=True, blank=True, verbose_name="Credit Card Interest Ratios")

    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='ccinterestratio_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='ccinterestratio_update_user')

    class Meta:
        verbose_name = 'KK Faiz Oranı'
        verbose_name_plural = 'KK Faiz Oranları'

    def __int__(self):
        return self.id


class SearchLog(models.Model):
    otel = models.ForeignKey('otels.Otel', verbose_name="Otel",
                             on_delete=models.DO_NOTHING, blank=True, null=True)
    keywords = models.CharField(
        max_length=250, verbose_name="keywords", blank=True, null=True)
    startDate = models.DateField(blank=True, null=True)
    finishDate = models.DateField(blank=True, null=True)
    childCondition = models.CharField(
        max_length=250, verbose_name="childCondition", blank=True, null=True)
    adultCount = models.IntegerField(blank=True, null=True)
    childCount = models.IntegerField(blank=True, null=True)
    response = JSONField(null=True, blank=True, verbose_name="Search Response")
    otelsFound = models.IntegerField(
        blank=True, null=True, verbose_name="Number of otels Found")
    pricesFound = models.IntegerField(
        blank=True, null=True, verbose_name="Number of prices Found")

    isActive = models.BooleanField(default=True, verbose_name="Is Active")
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", blank=True)
    createdby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Created By User",
                                  related_name='searchlog_create_user')
    updatedby = models.ForeignKey(User, on_delete=models.DO_NOTHING, default=1, verbose_name="Updated By User",
                                  related_name='searchlog_update_user')

    class Meta:
        verbose_name = 'Arama Logu'
        verbose_name_plural = 'Arama Logları'

    def __int__(self):
        return self.id


class BrokenPrice(models.Model):
    otel = models.ForeignKey('otels.Otel', verbose_name="Otel",
                             on_delete=models.CASCADE, null=True, blank=True)
    roomType = models.ForeignKey(
        'accomodations.RoomType',  on_delete=models.CASCADE, null=True, blank=True)
    pensionType = models.ForeignKey('accomodations.PensionType', on_delete=models.CASCADE,
                                    null=True, blank=True)
    # 1--> fiyat, 2--> aksiyon
    module = models.IntegerField(null=True, blank=True)
    priceId = models.IntegerField(null=True, blank=True)
    actionPriceId = models.IntegerField(null=True, blank=True)
    accomodationStartDate = models.DateField(null=True, blank=True)
    accomodationEndDate = models.DateField(null=True, blank=True)
    saleStartDate = models.DateField(null=True, blank=True)
    saleEndDate = models.DateField(null=True, blank=True)
    priceDays = ArrayField(models.IntegerField(), null=True, blank=True)
    # 1--> Net, 2--> Komisyonlu
    priceCalcType = models.IntegerField(null=True, blank=True)
    perPersonPrice = models.FloatField(null=True, blank=True)
    comissionRate = models.FloatField(null=True, blank=True)
    # 1--> Giriş, 2--> Konaklama
    base = models.IntegerField(null=True, blank=True)
    ebId = models.IntegerField(null=True, blank=True)
    ebRate = models.FloatField(null=True, blank=True)
    # 1--> Giriş, 2--> Konaklama
    ebBase = models.IntegerField(null=True, blank=True)
    # 1--> Kademeli, 2--> Kümülatif
    ebComissionType = models.IntegerField(null=True, blank=True)
    ebValidDays = ArrayField(models.IntegerField(), null=True, blank=True)
    ebExcludeDates = ArrayField(models.DateField(), null=True, blank=True)
    spoId = models.IntegerField(null=True, blank=True)
    spoRate = models.FloatField(null=True, blank=True)
    # 1--> Giriş, 2--> Konaklama
    spoBase = models.IntegerField(null=True, blank=True)
    # 1--> Kademeli, 2--> Kümülatif
    spoComissionType = models.IntegerField(null=True, blank=True)
    spoValidDays = ArrayField(models.IntegerField(), null=True, blank=True)
    spoExcludeDates = ArrayField(models.DateField(), null=True, blank=True)
    totalComissionPrice = models.FloatField(null=True, blank=True)
    netCost = models.FloatField(null=True, blank=True)
    profitMargin = models.FloatField(null=True, blank=True)
    salePrice = models.FloatField(null=True, blank=True)
    posterDiscountRate = models.FloatField(null=True, blank=True)
    posterPrice = models.FloatField(null=True, blank=True)
    realProfit = models.FloatField(null=True, blank=True)
    salesChannel = ArrayField(models.IntegerField(), null=True, blank=True)
    totalMinDays = models.IntegerField(null=True, blank=True)
    totalMaxDays = models.IntegerField(null=True, blank=True)
    priceMinDays = models.IntegerField(null=True, blank=True)
    priceMaxDays = models.IntegerField(null=True, blank=True)
    priceTemplateId = models.IntegerField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    created = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name="Create Date", null=True, blank=True)
    updated = models.DateTimeField(
        auto_now=True, editable=False, verbose_name="Update Date", null=True, blank=True)
    createdBy = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True,
                                  blank=True, related_name='%(app_label)s_%(class)s_created_by')
    updatedBy = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True,
                                  blank=True, related_name='%(app_label)s_%(class)s_updated_by')

    class Meta:
        db_table = 'brokenprice'
        verbose_name = 'brokenprice'
        verbose_name_plural = 'brokenprices'

    def __str__(self):
        return str(self.id)
