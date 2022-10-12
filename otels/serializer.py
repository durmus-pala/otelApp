from accomodations.models import PriceTemplateDetail, PriceDetails
from django.forms.models import model_to_dict
import ast
import json
from cities_light.contrib.restframework3 import CountrySerializer, RegionSerializer, SubRegionSerializer, CitySerializer
from cities_light.models import Country, Region, SubRegion, City
from actions.serializer import SalesChannelSerializer
from rest_framework import serializers
from otels.models import *
from actions.models import SalesChannel
from accomodations.models import inDays, Currency
from accomodations.serializer import RoomTypeGetSerializerOnlyName, PensionTypeSerializer


class CurrencySerialiser(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'
# from accomodations.serializer import inDaysSerialiser


class inDaysSerialiser(serializers.ModelSerializer):
    class Meta:
        model = inDays
        fields = '__all__'


class SupplierSerializer2(serializers.ModelSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField(required=False)

    class Meta:
        model = Supplier
        fields = ['id', 'title']


class OtelCategorySerializer2(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(required=False)

    class Meta:
        model = OtelCategory
        fields = ['id', 'name']


class OtelThemeSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtelTheme
        fields = '__all__'


class OtelThemeSerializer2(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(required=False)
    name_en = serializers.CharField(required=False)
    name_ru = serializers.CharField(required=False)

    class Meta:
        model = OtelTheme
        fields = ["id", "name", "name_en", "name_ru"]


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = '__all__'


class AirportSerializer2(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(required=False)

    class Meta:
        model = Airport
        fields = ["id", "name"]


class SalesChannelSerializer2(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(required=False)

    class Meta:
        model = SalesChannel
        fields = ["id", "name"]


class OtelSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer2(many=True, required=False, read_only=False)
    category = OtelCategorySerializer2(
        many=True, required=False, read_only=False)
    theme = OtelThemeSerializer2(many=True, required=False, read_only=False)
    airport = AirportSerializer2(many=True, required=False, read_only=False)
    salesChannel = SalesChannelSerializer2(
        many=True, required=False, read_only=False)
    contract = serializers.SerializerMethodField()
    activePriceCount = serializers.SerializerMethodField()

    class Meta:
        model = Otel
        fields = '__all__'

    def get_contract(self, instance):
        relatedContracts = Contract.objects.filter(
            isActive=True, otel__id=instance.id).values("id", "otel__id", "contractType")
        return relatedContracts

    def get_activePriceCount(self, instance):
        relatedPriceCount = len(PriceDetails.objects.filter(
            isActive=True, isStatusActive=True, otel__id=instance.id))
        return relatedPriceCount

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            representation["otelChain"] = {
                "id": OtelChainSerializer(instance.otelChain).data["id"],
                "name": OtelChainSerializer(instance.otelChain).data["name"],
            }
        except:
            pass
        try:
            representation["otelType"] = {
                "id": OtelChainSerializer(instance.otelType).data["id"],
                "name": OtelChainSerializer(instance.otelType).data["name"],
            }
        except:
            pass
        try:
            representation["country"] = {
                "id": CountrySerializer(instance.country).data["id"],
                "name": CountrySerializer(instance.country).data["name"],
            }
        except:
            pass
        try:
            representation["region"] = {
                "id": RegionSerializer(instance.region).data["id"],
                "name": RegionSerializer(instance.region).data["name"],
            }
        except:
            pass
        try:
            representation["subRegion"] = {
                "id": SubRegionSerializer(instance.subRegion).data["id"],
                "name": SubRegionSerializer(instance.subRegion).data["name"],
            }
        except:
            pass
        try:
            representation["location"] = {
                "id": CitySerializer(instance.location).data["id"],
                "name": CitySerializer(instance.location).data["name"],
            }
        except:
            pass
        return representation

    def create(self, validated_data):
        # To create manyToMany related fields
        supplier = validated_data.pop('supplier', [])
        category = validated_data.pop('category', [])
        theme = validated_data.pop('theme', [])
        airport = validated_data.pop('airport', [])
        salesChannel = validated_data.pop('salesChannel', [])
        supplierList = []
        categoryList = []
        themeList = []
        airportList = []
        salesChannelList = []
        obj = super().create(validated_data)

        if supplier:
            for eachSupplier in supplier:
                supplierList.append(dict(eachSupplier))

            for eachListedSupplier in supplierList:
                supplier_qs = Supplier.objects.filter(
                    id=eachListedSupplier["id"])

                if supplier_qs.exists():
                    lastSupplier = supplier_qs.first()
                else:
                    lastSupplier = Supplier.objects.create(
                        **eachSupplier)
                obj.supplier.add(lastSupplier)

        if category:
            for eachCategory in category:
                categoryList.append(dict(eachCategory))

            for eachListedCategory in categoryList:
                category_qs = OtelCategory.objects.filter(
                    id=eachListedCategory["id"])

                if category_qs.exists():
                    lastCategory = category_qs.first()
                else:
                    lastCategory = OtelCategory.objects.create(
                        **eachCategory)
                obj.category.add(lastCategory)

        if theme:
            for eachTheme in theme:
                themeList.append(dict(eachTheme))

            for eachListedTheme in themeList:
                theme_qs = OtelTheme.objects.filter(
                    id=eachListedTheme["id"])

                if theme_qs.exists():
                    lastTheme = theme_qs.first()
                else:
                    lastTheme = OtelTheme.objects.create(
                        **eachTheme)
                obj.theme.add(lastTheme)

        if airport:
            for eachAirport in airport:
                airportList.append(dict(eachAirport))

            for eachListedAirport in airportList:
                airport_qs = Airport.objects.filter(
                    id=eachListedAirport["id"])

                if airport_qs.exists():
                    lastAirport = airport_qs.first()
                else:
                    lastAirport = Airport.objects.create(
                        **eachAirport)
                obj.airport.add(lastAirport)

        if salesChannel:
            for eachSalesChannel in salesChannel:
                salesChannelList.append(dict(eachSalesChannel))

            for eachListedSalesChannel in salesChannelList:
                salesChannel_qs = SalesChannel.objects.filter(
                    id=eachListedSalesChannel["id"])

                if salesChannel_qs.exists():
                    lastSalesChannel = salesChannel_qs.first()
                else:
                    lastSalesChannel = SalesChannel.objects.create(
                        **eachSalesChannel)
                obj.salesChannel.add(lastSalesChannel)

        return obj

    def update(self, instance, validated_data):
        # To update manyToMany related fields
        if (bool(isinstance(self.initial_data.get('supplier'), list))):
            supplierData = validated_data.pop('supplier')
            supplierList = []
            instance.supplier.clear()

            for supplier in supplierData:
                supplierList.append(dict(supplier))

            for eachSupplier in supplierList:
                supplier_qs = Supplier.objects.filter(
                    id=eachSupplier["id"])

                if supplier_qs.exists():
                    suppliers = supplier_qs.first()
                else:
                    suppliers = Supplier.objects.create(
                        **eachSupplier)

                instance.supplier.add(suppliers)
        if (bool(isinstance(self.initial_data.get('category'), list))):
            categoryData = validated_data.pop('category')
            categoryList = []
            instance.category.clear()

            for category in categoryData:
                categoryList.append(dict(category))

            for eachCategory in categoryList:
                category_qs = OtelCategory.objects.filter(
                    id=eachCategory["id"])

                if category_qs.exists():
                    categories = category_qs.first()
                else:
                    categories = OtelCategory.objects.create(
                        **eachCategory)

                instance.category.add(categories)

        if (bool(isinstance(self.initial_data.get('theme'), list))):
            themeData = validated_data.pop('theme')
            themeList = []
            instance.theme.clear()

            for theme in themeData:
                themeList.append(dict(theme))

            for eachTheme in themeList:
                theme_qs = OtelTheme.objects.filter(
                    id=eachTheme["id"])

                if theme_qs.exists():
                    themes = theme_qs.first()
                else:
                    themes = OtelTheme.objects.create(
                        **eachTheme)

                instance.theme.add(themes)
        if (bool(isinstance(self.initial_data.get('airport'), list))):
            airportData = validated_data.pop('airport')
            airportList = []
            instance.airport.clear()

            for airport in airportData:
                airportList.append(dict(airport))

            for eachAirport in airportList:
                airport_qs = Airport.objects.filter(
                    id=eachAirport["id"])

                if airport_qs.exists():
                    airports = airport_qs.first()
                else:
                    airports = Airport.objects.create(
                        **eachAirport)

                instance.airport.add(airports)
        if (bool(isinstance(self.initial_data.get('salesChannel'), list))):
            salesChannelData = validated_data.pop('salesChannel')
            salesChannelList = []
            instance.salesChannel.clear()

            for salesChannel in salesChannelData:
                salesChannelList.append(dict(salesChannel))

            for eachSalesChannel in salesChannelList:
                salesChannel_qs = SalesChannel.objects.filter(
                    id=eachSalesChannel["id"])

                if salesChannel_qs.exists():
                    salesChannels = salesChannel_qs.first()
                else:
                    salesChannels = SalesChannel.objects.create(
                        **eachSalesChannel)

                instance.salesChannel.add(salesChannels)
        instance = super().update(instance, validated_data)
        return instance


class OtelSerializerOnlyName(serializers.ModelSerializer):
    class Meta:
        model = Otel
        fields = ['id', 'name']


class ModuleFormFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleFormFeatures
        fields = '__all__'


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = '__all__'


class OtelCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelCategory
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contract
        fields = '__all__'


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'


class PaymentPlanGetSerializer(serializers.ModelSerializer):
    # paymentMethod = PaymentMethodSerializer(many=True)
    class Meta:
        model = PaymentPlan
        fields = '__all__'


class PaymentPlanPostSerializer(serializers.ModelSerializer):
    # paymentMethod = PaymentMethodSerializer(many=True)
    class Meta:
        model = PaymentPlan
        fields = '__all__'


class PayAtFacilityGetSerializer(serializers.ModelSerializer):
    inDays = inDaysSerialiser(many=True)

    # paymentMethod = PaymentMethodSerializer(many=True)
    class Meta:
        model = PayAtFacility
        fields = '__all__'


class PayAtFacilityPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayAtFacility
        fields = '__all__'


class StakeHolderContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = StakeHolderContact
        fields = '__all__'


class OtelOwnerGetSerializer(serializers.ModelSerializer):
    otel = OtelSerializer()

    class Meta:
        model = OtelOwnership
        fields = '__all__'


class OtelOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelOwnership
        fields = '__all__'


class OtelServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelServiceCategory
        fields = '__all__'


class OtelFacilityDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelFacilityDetail
        fields = '__all__'


class OtelFeaturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelFeatures
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            representation["feature"] = {
                "id": OtelFacilityDetailSerializer(instance.feature).data["id"],
                "name": OtelFacilityDetailSerializer(instance.feature).data["name"],
                "name_en": OtelFacilityDetailSerializer(instance.feature).data["name_en"],
                "name_ru": OtelFacilityDetailSerializer(instance.feature).data["name_ru"],
                "isPrice": OtelFacilityDetailSerializer(instance.feature).data["isPrice"],
            }
        except:
            pass
        try:
            representation["feature"]["serviceCategory"] = {
                "id": OtelServiceCategory.objects.get(id=OtelFacilityDetailSerializer(instance.feature).data["serviceCategory"]).id,
                "name": OtelServiceCategory.objects.get(id=OtelFacilityDetailSerializer(instance.feature).data["serviceCategory"]).name,
                "name_en": OtelServiceCategory.objects.get(id=OtelFacilityDetailSerializer(instance.feature).data["serviceCategory"]).name_en,
                "name_ru": OtelServiceCategory.objects.get(id=OtelFacilityDetailSerializer(instance.feature).data["serviceCategory"]).name_ru,
            }
        except:
            representation["feature"]["serviceCategory"] = None
        return representation


class OtelImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelImages
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            representation["imageCategory"] = {
                "id": OtelServiceCategorySerializer(instance.imageCategory).data["id"],
                "name": OtelServiceCategorySerializer(instance.imageCategory).data["name"],
                "name_en": OtelServiceCategorySerializer(instance.imageCategory).data["name_en"],
                "name_ru": OtelServiceCategorySerializer(instance.imageCategory).data["name_ru"],
            }
        except:
            pass
        try:
            representation["roomType"] = {
                "id": RoomTypeGetSerializerOnlyName(instance.roomType).data["id"],
                "name": RoomTypeGetSerializerOnlyName(instance.roomType).data["name"],
            }
        except:
            pass
        return representation


class CustomerPaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPaymentType
        fields = '__all__'


class OtelContractPaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelContractPaymentType
        fields = '__all__'


class OtelServiceDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelServiceDescription
        fields = '__all__'


class PeriodicDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicDescription
        fields = '__all__'


class PensionTypePeriodicDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PensionTypePeriodicDescription
        fields = '__all__'


class PeriodicDescriptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicDescriptionType
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class OtelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelType
        fields = '__all__'


class OtelChainSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtelChain
        fields = '__all__'


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = '__all__'


class BankForPaymentAccountInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        # fields = '__all__'
        fields = ['name', 'logoImage']


class PaymentAccountInfoGetSerializer(serializers.ModelSerializer):
    bank = BankSerializer()

    class Meta:
        model = PaymentAccountInfo
        fields = '__all__'


class PaymentAccountInfoPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAccountInfo
        fields = '__all__'


class AccountInfoSerializer(serializers.ModelSerializer):
    bank = BankSerializer()
    currencyType = CurrencySerialiser()

    class Meta:
        model = AccountInfo
        fields = '__all__'


class AccountInfoPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountInfo
        fields = '__all__'


class OtelSerializerforHotelGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Otel
        # fields = '__all__'
        fields = ['id',
                  'name']


class HotelGroupPostSerializer(serializers.ModelSerializer):
    # otel = OtelSerializerforHotelGroupSerializer(many=True)
    class Meta:
        model = HotelGroup
        fields = '__all__'


class ContractItemsApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractItemsApproval
        fields = '__all__'


class ChilConditionThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChilConditionTheme
        fields = '__all__'


class SearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchLog
        fields = '__all__'


class HotelGroupGetSerializer(serializers.ModelSerializer):
    otel = OtelSerializerforHotelGroupSerializer(many=True)

    class Meta:
        model = HotelGroup
        fields = '__all__'


class EpidemicMeasuresReadSerializer(serializers.ModelSerializer):
    measuresJSON = serializers.SerializerMethodField(read_only=True)

    def get_measuresJSON(self, obj):
        import json
        if obj.measuresJSON != None:
            return json.loads(obj.measuresJSON)
        else:
            return ""

    class Meta:
        model = EpidemicMeasures
        fields = '__all__'


class EpidemicMeasuresPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = EpidemicMeasures
        fields = '__all__'


class OtelForCCInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Otel
        fields = ['id', 'name']


class BankForCCInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['id', 'name']


class CCInterestRatioReadSerializer(serializers.ModelSerializer):
    # interestRatios = serializers.SerializerMethodField(read_only=True)
    # def get_interestRatios(self, obj):
    #     import json
    #     if obj.interestRatios !=None:
    #         return json.loads(obj.interestRatios)
    #     else:
    #         return ""
    bank = BankForCCInterestSerializer()
    otel = OtelForCCInterestSerializer()

    class Meta:
        model = CCInterestRatio
        fields = '__all__'


class CCInterestRatioPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CCInterestRatio
        fields = '__all__'


class InvoiceInfoReadSerializer(serializers.ModelSerializer):
    region = serializers.SerializerMethodField()
    subRegion = serializers.SerializerMethodField()

    def get_region(self, instance):
        try:
            s = (Region.objects.get(pk=instance.region_id))
        except Region.DoesNotExist:
            return None
        dict_obj = model_to_dict(s)
        return dict_obj

    def get_subRegion(self, instance):
        try:
            s = (SubRegion.objects.get(pk=instance.subRegion_id))
        except SubRegion.DoesNotExist:
            return None
        dict_obj = model_to_dict(s)
        return dict_obj

    class Meta:
        model = InvoiceInfo
        fields = '__all__'


class InvoiceInfoPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceInfo
        fields = '__all__'


class OtelChainSerializer2(serializers.ModelSerializer):
    class Meta:
        model = OtelChain
        fields = ['id', 'name']


class OtelReadSerializer2(serializers.ModelSerializer):
    supplier = SupplierSerializer2(read_only=True, many=True)
    category = OtelCategorySerializer2(read_only=True, many=True)
    otelChain = OtelChainSerializer2(read_only=True, many=False)

    class Meta:
        model = Otel
        fields = '__all__'


class OtelReadSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True, many=True)
    category = OtelCategorySerializer(read_only=True, many=True)
    theme = OtelThemeSerializer(read_only=True, many=True)
    airport = AirportSerializer(read_only=True, many=True)
    salesChannel = SalesChannelSerializer(read_only=True, many=True)
    otelChain = OtelChainSerializer(read_only=True, many=False)
    country = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    subRegion = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    distancesToPOIS = serializers.JSONField()
    extraFeatures = serializers.JSONField()
    stakeholders = serializers.SerializerMethodField()
    otelfeatures = serializers.SerializerMethodField()
    otelservicedescriptions = serializers.SerializerMethodField()
    periodicdescriptions = serializers.SerializerMethodField()
    pensiontypeperiodicdescriptions = PensionTypePeriodicDescriptionSerializer(
        read_only=True, many=True)
    freeKidConds = serializers.SerializerMethodField()

    def get_freeKidConds(self, instance):
        freeKidConds = []
        freeKidCondsIDs = []
        ptds = PriceTemplateDetail.objects.filter(otel_id=instance.id)
        for ptd in ptds:
            fcs = ptd.freeKidConditionsList.values('id', 'name').all()
            if fcs:
                for fc in fcs:
                    if fc['id'] not in freeKidCondsIDs:
                        freeKidCondsIDs.append(fc['id'])
                        freeKidConds.append({
                            'id': fc['id'],
                            'name': fc['name']
                        })

        print(freeKidConds)

        return freeKidConds

    def get_country(self, instance):
        try:
            s = (Country.objects.get(pk=instance.country_id))
        except Country.DoesNotExist:
            return None
        dict_obj = model_to_dict(s)
        return dict_obj

    def get_region(self, instance):
        try:
            s = (Region.objects.get(pk=instance.region_id))
        except Region.DoesNotExist:
            return None
        dict_obj = model_to_dict(s)
        return dict_obj

    def get_subRegion(self, instance):
        try:
            s = (SubRegion.objects.get(pk=instance.subRegion_id))
        except SubRegion.DoesNotExist:
            return None
        dict_obj = model_to_dict(s)
        return dict_obj

    def get_location(self, instance):
        try:
            s = (City.objects.get(pk=instance.location_id))
        except City.DoesNotExist:
            return None
        dict_obj = model_to_dict(s)
        return dict_obj

    def get_stakeholders(self, instance):
        s = (StakeHolderContact.objects.filter(otel_id=instance.id, isActive=True).values('id', 'title', 'fullName',
                                                                                          'phone', 'email'))
        json_posts = ast.literal_eval(json.dumps(list(s)))
        return json_posts

    def get_otelfeatures(self, instance):
        s = (OtelFeatures.objects.filter(otel_id=instance.id, isActive=True).values('id', 'feature',
                                                                                    'feature__serviceCategory'))
        json_posts = ast.literal_eval(json.dumps(list(s)))
        return json_posts

    def get_otelservicedescriptions(self, instance):
        s = (OtelServiceDescription.objects.filter(otel_id=instance.id, isActive=True).values('id', 'serviceCategory',
                                                                                              'descscription'))
        json_posts = ast.literal_eval(json.dumps(list(s)))
        return json_posts

    def get_periodicdescriptions(self, instance):
        s = (PeriodicDescription.objects.filter(otel_id=instance.id, isActive=True).values('id', 'startDate',
                                                                                           'finishDate',
                                                                                           'descriptionType',
                                                                                           'description', 'title'))
        json_posts = ast.literal_eval(json.dumps(list(s), default=str))
        # return json.dumps(
        #     item,
        #     sort_keys=True,
        #     indent=1,
        #     cls=DjangoJSONEncoder
        # )
        return json_posts

    #
    # def get_pensiontypeperiodicdescriptions(self, instance):
    #     s = (PensionTypePeriodicDescription.objects.filter(otel_id=instance.id, isActive=True).values('id','startDate','finishDate','pensionType','description', 'title'))
    #     json_posts = ast.literal_eval(json.dumps(list(s), default=str))
    #     return json_posts

    class Meta:
        model = Otel
        fields = [
            'id',
            'name',
            'erpNo',
            'description',
            'operationNote',
            'address',
            'email',
            'seoText',
            'supplierNotes',
            'phone1',
            'phone2',
            'latitude',
            'longitude',
            'isStatusActive',
            'otelChain',
            'ytLink',
            'extraFeatures',
            'distancesToPOIS',
            'otelType',
            'country',
            'region',
            'subRegion',
            'location',
            'supplier',
            'category',
            'theme',
            'airport',
            'salesChannel',
            'stakeholders',
            'otelfeatures',
            'otelservicedescriptions',
            'periodicdescriptions',
            'pensiontypeperiodicdescriptions',
            'freeKidConds'
        ]


class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFile
        fields = '__all__'


class BrokenPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrokenPrice
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        try:
            representation["otel"] = {
                "id": OtelSerializer(instance.otel).data["id"],
                "name": OtelSerializer(instance.otel).data["name"],
            }
        except:
            pass
        try:
            representation["roomType"] = {
                "id": RoomTypeGetSerializerOnlyName(instance.roomType).data["id"],
                "name": RoomTypeGetSerializerOnlyName(instance.roomType).data["name"],
            }
        except:
            pass
        try:
            representation["pensionType"] = {
                "id": PensionTypeSerializer(instance.pensionType).data["id"],
                "name": PensionTypeSerializer(instance.pensionType).data["name"],
            }
        except:
            pass
        return representation
