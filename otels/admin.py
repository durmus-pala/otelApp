from django.contrib import admin
from otels.models import *


class OtelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone1', 'phone2', 'slug')
    list_filter = ('isActive',)
    ordering = ('-id',)
    search_fields = ('id', 'name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelChainAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    ordering = ('-id',)
    search_fields = ('id', 'name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    ordering = ('-id',)
    search_fields = ('id', 'name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    ordering = ('-id',)
    search_fields = ('id', 'name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'isMain', 'isOtel', 'isTour', 'isTransfer')
    list_filter = ('isMain', 'isOtel', 'isTour')
    ordering = ('-id',)
    search_fields = ('id', 'name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class AirportAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'latitude', 'longitude')
    ordering = ('-id',)
    search_fields = ('id', 'name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'startDate', 'finishDate', 'isPurchasePrice')
    ordering = ('-id',)
    search_fields = ('id', 'otel__name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50
    date_hierarchy = 'finishDate'


class StakeHolderContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'fullName', 'title', 'phone', 'email', 'otel')
    ordering = ('-id',)
    search_fields = ('id', 'otel__name', 'email', 'phone')
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('-id',)
    search_fields = ('id', 'admin')
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelFacilityDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'serviceCategory', 'feature')
    ordering = ('-id',)
    search_fields = ('id', 'name')
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelFeaturesAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'get_servicecategory', 'feature')
    ordering = ('-id',)
    search_fields = ('id', 'feature')
    readonly_fields = ("created", "updated",)
    list_per_page = 50

    def get_servicecategory(self, obj):
        return obj.feature.serviceCategory


class OtelImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'imageCategory', 'roomType',
                    'isDefault', 'isActive', 'title')
    ordering = ('-id',)
    search_fields = ('id', 'imageCategory')
    readonly_fields = ("created", "updated",)


class CustomerPaymentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('-id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelContractPaymentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('-id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class OtelServiceDescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'serviceCategory')
    ordering = ('-id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class PeriodicDescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'descriptionType', 'startDate', 'finishDate')
    ordering = ('-id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class PensionTypePeriodicDescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'pensionType',
                    'title', 'startDate', 'finishDate')
    ordering = ('-id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class PeriodicDescriptionTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    ordering = ('-id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    ordering = ('-id',)
    search_fields = ('id', 'title')
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class PayAtFacilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'startDate', 'finishDate', 'isActive')
    ordering = ('-id',)
    search_fields = ('id', 'contract',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'day', 'date',
                    'paymentPercentage', 'isActive')
    ordering = ('-id',)
    search_fields = ('id', 'contract',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    ordering = ('-id',)
    search_fields = ('id', 'name',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


#
class OtelOwnershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'ownerlist')
    # list_display = ('id','otel', 'getowners')
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50

    def ownerlist(self, obj):
        return list(obj.owners.values_list('username', flat=True).all())


class ModuleFormFeaturesAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel',)
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class BankAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class AccountInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'bank', 'commissionRate')
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class HotelGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'groupName', )
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class PaymentAccountInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'bank', )
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class EpidemicMeasuresAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel')
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class InvoiceInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'title', 'region')
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class ContractItemsApprovalAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'item1', 'item2', 'item3', )
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class CCInterestRatioAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'bank', )
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class ChilConditionThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'name', 'childCondition', 'ratio')
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'keywords', 'startDate', 'finishDate',
                    'childCount', 'childCount', 'otelsFound', 'pricesFound')
    ordering = ('-id',)
    search_fields = ('id',)
    readonly_fields = ("created", "updated",)
    list_per_page = 50


class UploadFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'isActive')
    list_filter = ('id', 'file', 'isActive')
    ordering = ('-id',)
    search_fields = ('id', 'file', 'isActive')
    list_per_page = 50


class BrokenPriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'otel', 'roomType', 'pensionType',
                    'module', 'priceId', 'actionPriceId')
    list_filter = ('id', 'otel', 'roomType', 'pensionType',
                   'module', 'priceId', 'actionPriceId')
    ordering = ('-id',)
    search_fields = ('id', )
    list_per_page = 50


admin.site.register(SearchLog, SearchLogAdmin)
admin.site.register(ChilConditionTheme, ChilConditionThemeAdmin)
admin.site.register(CCInterestRatio, CCInterestRatioAdmin)
admin.site.register(ContractItemsApproval, ContractItemsApprovalAdmin)
admin.site.register(InvoiceInfo, InvoiceInfoAdmin)
admin.site.register(EpidemicMeasures, EpidemicMeasuresAdmin)
admin.site.register(PaymentAccountInfo, PaymentAccountInfoAdmin)
admin.site.register(HotelGroup, HotelGroupAdmin)
admin.site.register(Bank, BankAdmin)
admin.site.register(AccountInfo, AccountInfoAdmin)
admin.site.register(ModuleFormFeatures, ModuleFormFeaturesAdmin)
admin.site.register(OtelOwnership, OtelOwnershipAdmin)
admin.site.register(Otel, OtelAdmin)
admin.site.register(OtelChain, OtelChainAdmin)
admin.site.register(OtelCategory, OtelCategoryAdmin)
admin.site.register(Airport, AirportAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(StakeHolderContact, StakeHolderContactAdmin)
admin.site.register(OtelServiceCategory, OtelServiceCategoryAdmin)
admin.site.register(OtelFacilityDetail, OtelFacilityDetailAdmin)
admin.site.register(OtelImages, OtelImagesAdmin)
admin.site.register(CustomerPaymentType, CustomerPaymentTypeAdmin)
admin.site.register(OtelContractPaymentType, OtelContractPaymentTypeAdmin)
admin.site.register(OtelFeatures, OtelFeaturesAdmin)
admin.site.register(OtelTheme, OtelThemeAdmin)
admin.site.register(OtelType, OtelTypeAdmin)
admin.site.register(OtelServiceDescription, OtelServiceDescriptionAdmin)
admin.site.register(PeriodicDescription, PeriodicDescriptionAdmin)
admin.site.register(PensionTypePeriodicDescription,
                    PensionTypePeriodicDescriptionAdmin)
admin.site.register(PeriodicDescriptionType, PeriodicDescriptionTypeAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(PayAtFacility, PayAtFacilityAdmin)
admin.site.register(PaymentPlan, PaymentPlanAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(UploadFile, UploadFileAdmin)
admin.site.register(BrokenPrice, BrokenPriceAdmin)
