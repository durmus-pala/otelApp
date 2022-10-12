
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend, BaseInFilter, NumberFilter, FilterSet
from rest_framework_tracking.mixins import LoggingMixin

from inline.imports_all import *
from otels.paginations import *
from otels.serializer import *
from otels.models import *
from otels.utils import PriceCostInfoFunctions, ReservationSearchFunctions

from rest_framework.parsers import JSONParser
from rest_framework.generics import RetrieveAPIView

from functools import reduce
import operator
from django.db.models import Q
from datetime import timedelta
from accomodations.models import *
from actions.models import *
from booking.models import *
from management.models import CountryGrouping, CurrencyCountryGroup

import base64
from django.core.files.base import ContentFile
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from datetime import datetime, timedelta
from iteration_utilities import unique_everseen
from collections import defaultdict
from django.db import transaction


class OtelMiniList(LoggingMixin, ListAPIView):
    serializer_class = OtelSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['icontains'],
        'region_text': ['icontains'],
        'subRegion_text': ['icontains'],
        'location_text': ['icontains'],
        'category__name': ['icontains'],
        'theme__name': ['icontains'],
        'airport__code': ['exact'],
        'slug': ['exact'],

    }
    search_fields = ['name', 'region_text', 'subRegion_text']
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = Otel.objects.filter(isStatusActive=True, isActive=True)
        return queryset


class OtelList(ListAPIView, CreateModelMixin):
    serializer_class = OtelSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'region__id': ['exact'],
        'airport__id': ['in'],
        'category__id': ['in'],
        'location__id': ['exact'],
        'isStatusActive': ['exact'],
    }
    search_fields = ('id', 'name', 'region__name',
                     'location__name', 'category__name', 'airport__name')
    ordering = ['-id']
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = Otel.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelSerializer(
            data=request.data, many=many)
        # Otel Name must be unique
        try:
            if Otel.objects.filter(isActive=True, name=serializer.initial_data["name"]).exists():
                responseData = {
                    "status": status.HTTP_409_CONFLICT,
                    "message": "Aynı isimde Otel bulunmaktadır! Lütfen listeleme ekranından ilgili oteli kontrol ediniz."
                }
                return Response(responseData, status=status.HTTP_200_OK)
        except:
            pass
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OtelChange(DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = Otel.objects.filter(isActive=True)
    serializer_class = OtelSerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        # otelName must be unique
        try:
            if (Otel.objects.filter(isActive=True, name=serializer.initial_data["name"]).exists()) and (instance.name != serializer.initial_data["name"]):
                responseData = {
                    "status": status.HTTP_409_CONFLICT,
                    "message": "Aynı isimde Otel bulunmaktadır! Lütfen listeleme ekranından ilgili oteli kontrol ediniz."
                }
                return Response(responseData, status=status.HTTP_200_OK)
        except:
            pass
        self.perform_update(serializer)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        if serializer.is_valid():
            serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class EpidemicMeasuresList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = EpidemicMeasuresReadSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ['id', 'otel']
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = EpidemicMeasures.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = EpidemicMeasuresPostSerializer(
            data=request.data, many=many)

        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni Salgın Hastalık Tedbiri oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Salgın Hastalık Tedbiri oluşturulamadı'
            }
        return JsonResponse(responseData)


class EpidemicMeasuresChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = EpidemicMeasures.objects.all()
    serializer_class = EpidemicMeasuresReadSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = EpidemicMeasuresPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Salgın Hastalık Tedbiri silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        # simdi nesnenin kendisini silelim
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class SearchLogList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = SearchLogSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ['id', 'otel']
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = SearchLog.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = SearchLogSerializer(data=request.data, many=many)

        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni arama logu oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Arama logu oluşturulamadı'
            }
        return JsonResponse(responseData)


class SearchLogChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = SearchLog.objects.all()
    serializer_class = SearchLogSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = SearchLogSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Arama logu silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        # simdi nesnenin kendisini silelim
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class CCInterestRatioList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = CCInterestRatioReadSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'bank': ['exact'],
    }
    search_fields = ['id', 'otel']
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = CCInterestRatio.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = CCInterestRatioPostSerializer(
            data=request.data, many=many)

        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'KK Faiz oranlari tablosu oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'KK Faiz oranlari tablosu oluşturulamadı'
            }
        return JsonResponse(responseData)


class CCInterestRatioChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = CCInterestRatio.objects.all()
    serializer_class = CCInterestRatioReadSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = CCInterestRatioPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'KK Faiz oranlari tablosu silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        # simdi nesnenin kendisini silelim
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class ContractItemsApprovalList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = ContractItemsApprovalSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ['id', 'otel']
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = ContractItemsApproval.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = ContractItemsApprovalSerializer(
            data=request.data, many=many)

        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Kontrat maddeleri olusuturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Kontrat maddeleri oluşturulamadı'
            }
        return JsonResponse(responseData)


class ContractItemsApprovalChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = ContractItemsApproval.objects.all()
    serializer_class = ContractItemsApprovalSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = ContractItemsApprovalSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Kontrat maddeleri silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        # simdi nesnenin kendisini silelim
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class InvoiceInfoList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = InvoiceInfoReadSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ['id', 'otel']
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = InvoiceInfo.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = InvoiceInfoPostSerializer(data=request.data, many=many)

        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Fatura bilgisi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Fatura bilgisi oluşturulamadı'
            }
        return JsonResponse(responseData)


class InvoiceInfoChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = InvoiceInfo.objects.all()
    serializer_class = InvoiceInfoReadSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = EpidemicMeasuresPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Fatura bilgisi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        # simdi nesnenin kendisini silelim
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class OwnerReportFilter(FilterSet):
    owners = NumberInFilter(field_name='owners', lookup_expr='in')

    class Meta:
        model = OtelOwnership
        fields = {
            'id': ['exact'],
            'otel': ['exact', 'in'],
        }


class OtelOwnerList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelOwnerGetSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_class = OwnerReportFilter
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['-id']

    def get_queryset(self):
        queryset = OtelOwnership.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelOwnerSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'OtelOwner oluşturulamadı'
            }
            return JsonResponse(responseData)


class OtelOwnerChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelOwnership.objects.all()
    serializer_class = OtelOwnerSerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Modul form özelliği silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class ModuleFormFeatureList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = ModuleFormFeatureSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ('id', 'otel')
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = ModuleFormFeatures.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = ModuleFormFeatureSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Modul form özelliği oluşturulamadı'
            }
            return JsonResponse(responseData)


class ModuleFormFeatureChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = ModuleFormFeatures.objects.all()
    serializer_class = ModuleFormFeatureSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Modul form özelliği silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class ModuleFormFeatureAnonim(LoggingMixin, RetrieveAPIView):
    # this api will be anonimous and implemnent GET/Retrieve only
    authentication_classes = []
    permission_classes = []

    queryset = ModuleFormFeatures.objects.all()
    serializer_class = ModuleFormFeatureSerializer
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            from django.contrib.gis.geoip2 import GeoIP2
            from geoip2.errors import AddressNotFoundError
            g = GeoIP2()
            client_ip = request.META['HTTP_X_REAL_IP']

            try:
                location = g.city(client_ip)
            except AddressNotFoundError:
                location = "No location"

            s = dict(serializer.data)
            s['location'] = location
            return Response(s)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)


class OtelChainList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelChainSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
    }
    search_fields = ('id', 'name')
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = OtelChain.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelChainSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel zinciri oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel zinciri oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelChainChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelChain.objects.all()
    serializer_class = OtelChainSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel zinciri silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelCategoryList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelCategorySerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
        'isMain': ['exact'],
        'isOtel': ['exact'],
        'isTour': ['exact'],
        'isTransfer': ['exact'],
    }
    search_fields = ('id', 'name',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = OtelCategory.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelCategorySerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel kategorisi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel kategorisi oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelCategoryChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelCategory.objects.all()
    serializer_class = OtelCategorySerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel kategorisi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class AirportList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = AirportSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
        'code': ['exact'],
        'country': ['exact'],
        'region': ['exact'],
        'subRegion': ['exact'],
        'location': ['exact'],
    }
    search_fields = ('id', 'name', 'code', 'country',
                     'region', 'subRegion', 'location', 'slug')
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = Airport.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = AirportSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni havaalanı oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Havaalanı oluşturulamadı'
            }
        return JsonResponse(responseData)


class AirportChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Havaalanı silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class ContractList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = ContractSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'startDate': ['gte', 'lte', 'exact'],
        'finishDate': ['gte', 'lte', 'exact'],
    }
    search_fields = ('id', 'otel',)
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = Contract.objects.filter(isActive=True).order_by('id')
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = ContractSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'id': serializer.data["id"],
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni kontrat oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Kontrat oluşturulamadı'
            }
        return JsonResponse(responseData)


class ContractChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Kontrat silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        # instance.patmentplans.all().update(isActive=False)
        # instance.payatfacilitychoices.all().update(isActive=False)
        # print(list(instance.patmentplans.all().values_list('id', flat=True)))
        # print(list(instance.payatfacilitychoices.all().values_list('id', flat=True)))
        # PayAtFacility.objects.filter(contract=instance.id).update(isActive=False)
        # PaymentPlan.objects.filter(contract=instance.id).update(isActive=False)
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class UploadFileList(ListAPIView, CreateModelMixin):
    serializer_class = UploadFileSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
    }
    search_fields = ('id', )
    ordering = ['-id']

    def get_queryset(self):
        queryset = UploadFile.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = UploadFileSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UploadFileChange(DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = UploadFile.objects.filter(isActive=True)
    serializer_class = UploadFileSerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class OtelServiceCategoryList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelServiceCategorySerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
    }
    search_fields = ('id', 'name',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = OtelServiceCategory.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelServiceCategorySerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel hizmet kategorisi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel hizmet kategorisi oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelServiceCategoryChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelServiceCategory.objects.all()
    serializer_class = OtelServiceCategorySerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel servis kategorisi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelTypeList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelTypeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
    }
    search_fields = ('id', 'name',)
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = OtelType.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelTypeSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel hizmet kategorisi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel hizmet kategorisi oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelTypeChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelType.objects.all()
    serializer_class = OtelTypeSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel Tipi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelFacilityDetailList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelFacilityDetailSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
        'serviceCategory': ['exact'],
        'feature': ['exact'],
        'isPrice': ['exact'],

    }
    search_fields = ('id', 'name', 'serviceCategory', 'feature')
    ordering_fields = '__all__'
    ordering = ['-id']

    #    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = OtelFacilityDetail.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelFacilityDetailSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel tesisi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel tesisi oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelFacilityDetailChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelFacilityDetail.objects.all()
    serializer_class = OtelFacilityDetailSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel tesisi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelFeaturesList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelFeaturesSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'feature': ['exact'],
        'feature__isPrice': ['exact'],
        'feature__serviceCategory__id': ['exact'],
    }
    search_fields = ('id', 'otel', 'feature')
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = OtelFeatures.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        print(request.data)
        print(request.data[0]['otel'])

        many = True if isinstance(request.data, list) else False
        serializer = OtelFeaturesSerializer(data=request.data, many=many)
        if serializer.is_valid():
            OtelFeatures.objects.filter(
                otel=request.data[0]['otel']).all().update(isActive=False)

            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel özelliği oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel özelliği oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelFeaturesChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelFeatures.objects.all()
    serializer_class = OtelFeaturesSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel özelliği silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelImagesList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelImagesSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'imageCategory': ['exact'],
        'isVideo': ['exact'],
        'roomType': ['exact', 'isnull'],
    }
    search_fields = ('id', 'otel', 'otelservice')
    ordering_fields = '__all__'
    ordering = ['imageOrder']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = OtelImages.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelImagesSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel resmi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel resmi oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelImagesChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelImages.objects.all()
    serializer_class = OtelImagesSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)


class CustomerPaymentTypeList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = CustomerPaymentTypeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
    }
    search_fields = ('id', 'name')
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = CustomerPaymentType.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = CustomerPaymentTypeSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Musteri Ödeme Aksiyonu oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Musteri Ödeme Aksiyonu oluşturulamadı'
            }
        return JsonResponse(responseData)


class CustomerPaymentTypeChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = CustomerPaymentType.objects.all()
    serializer_class = CustomerPaymentTypeSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Musteri Ödeme Aksiyonu silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelContractPaymentTypeList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelContractPaymentTypeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
    }
    search_fields = ('id', 'name')
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = OtelContractPaymentType.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelContractPaymentTypeSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Otel Ödeme Aksiyonu oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel Ödeme Aksiyonu oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelContractPaymentTypeChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelContractPaymentType.objects.all()
    serializer_class = OtelContractPaymentTypeSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel Ödeme Aksiyonu silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelThemeList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelThemeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
    }
    search_fields = ('id', 'name')
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = OtelTheme.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelThemeSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel teması oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel teması oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelThemeChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelTheme.objects.all()
    serializer_class = OtelThemeSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel teması silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class OtelServiceDescriptionList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = OtelServiceDescriptionSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'serviceCategory': ['exact'],
        'startDate': ['gte', 'lte', 'exact'],
        'finishDate': ['gte', 'lte', 'exact'],

    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = OtelServiceDescription.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = OtelServiceDescriptionSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            OtelServiceDescription.objects.filter(
                otel_id=request.data["otel"],
                serviceCategory=request.data["serviceCategory"]).update(isActive=False)
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel hizmetleri  açıklamasi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel hizmetleri açıklamasi oluşturulamadı'
            }
        return JsonResponse(responseData)


class OtelServiceDescriptionChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = OtelServiceDescription.objects.all()
    serializer_class = OtelServiceDescriptionSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel hizmetleri Açıklama silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class PeriodicDescriptionList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = PeriodicDescriptionSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'descriptionType': ['exact'],
    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PeriodicDescription.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = PeriodicDescriptionSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni dönemsel açıklama oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Dönemsel açıklama oluşturulamadı'
            }
        return JsonResponse(responseData)


class PeriodicDescriptionChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = PeriodicDescription.objects.all()
    serializer_class = PeriodicDescriptionSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Dönemsel Açıklama silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class PensionTypePeriodicDescriptionList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = PensionTypePeriodicDescriptionSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'pensionType': ['exact'],
        'startDate': ['gte', 'lte', 'exact'],
        'finishDate': ['gte', 'lte', 'exact'],
    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PensionTypePeriodicDescription.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = PensionTypePeriodicDescriptionSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni pansiyon tipi dönemsel açıklama oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Pansiyon tipi dönemsel açıklama oluşturulamadı'
            }
        return JsonResponse(responseData)


class PensionTypePeriodicDescriptionChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = PensionTypePeriodicDescription.objects.all()
    serializer_class = PensionTypePeriodicDescriptionSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Pansiyon tipi dönemsel Açıklama silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class PeriodicDescriptionTypeList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = PeriodicDescriptionTypeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PeriodicDescriptionType.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = PeriodicDescriptionTypeSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni dönemsel açıklama tipi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Dönemsel açıklama tipi oluşturulamadı'
            }
        return JsonResponse(responseData)


class PeriodicDescriptionTypeChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = PeriodicDescriptionType.objects.all()
    serializer_class = PeriodicDescriptionTypeSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Dönemsel Açıklama tipi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class StakeHolderContactList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = StakeHolderContactSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],

    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = StakeHolderContact.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = StakeHolderContactSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel yetkilisi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel yetkilisi oluşturulamadı'
            }
        return JsonResponse(responseData)


class StakeHolderContactChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = StakeHolderContact.objects.all()
    serializer_class = StakeHolderContactSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel yetkilisi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class SupplierList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = SupplierSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'title': ['exact'],
    }
    search_fields = ('id', 'title')
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = Supplier.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = SupplierSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni tedarikçi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Tedarikçi oluşturulamadı'
            }
        return JsonResponse(responseData)


class SupplierChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Tedarikçi tipi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class PayAtFacilityList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = PayAtFacilityGetSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'contract': ['exact'],
        'startDate': ['gte', 'lte', 'exact'],
        'finishDate': ['gte', 'lte', 'exact'],
    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PayAtFacility.objects.filter(isActive=True).order_by('id')
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = PayAtFacilityPostSerializer(data=request.data, many=many)
        if serializer.is_valid():
            contract = None
            if isinstance(request.data, list):
                contract = request.data[0]['contract']
            if isinstance(request.data, dict):
                contract = request.data['contract']
            # PayAtFacility.objects.filter(contract=contract).update(isActive=False)
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Tesiste ödeme seceneği oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Tesiste ödeme seceneği oluşturulamadı'
            }
        return JsonResponse(responseData)


class PayAtFacilityChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = PayAtFacility.objects.all()
    serializer_class = PayAtFacilityGetSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = PayAtFacilityPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Tesiste ödeme seceneği silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class PaymentPlanList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = PaymentPlanGetSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'contract': ['exact'],
        # 'paymentplan': ['exact'],
    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PaymentPlan.objects.filter(isActive=True).order_by('id')
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = PaymentPlanPostSerializer(data=request.data, many=many)
        if serializer.is_valid():
            contract = None
            if isinstance(request.data, list):
                contract = request.data[0]['contract']
            if isinstance(request.data, dict):
                contract = request.data['contract']
            # PaymentPlan.objects.filter(contract=contract).update(isActive=False)
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Ödeme Planı oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Ödeme Planı oluşturulamadı'
            }
        return JsonResponse(responseData)


class PaymentPlanChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = PaymentPlan.objects.all()
    serializer_class = PaymentPlanGetSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = PaymentPlanPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Ödeme Planı silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class BankList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = BankSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'name': ['exact'],
    }
    search_fields = ('id', 'name')
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = Bank.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = BankSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni banka  oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Banka oluşturulamadı'
            }
        return JsonResponse(responseData)


class BankChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Banka silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class AccountInfoList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = AccountInfoSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
        'bank': ['exact'],
    }
    search_fields = ('id', 'otel', 'bank')
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = AccountInfo.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = AccountInfoPostSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni banka hesabi  oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Banka hesabi oluşturulamadı'
            }
        return JsonResponse(responseData)


class AccountInfoChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = AccountInfo.objects.all()
    serializer_class = AccountInfoSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = AccountInfoPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Banka hesabi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class HotelGroupList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = HotelGroupGetSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'groupName': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ('id', 'otel', 'bank')
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = HotelGroup.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = HotelGroupPostSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel grubu oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel grubu oluşturulamadı'
            }
        return JsonResponse(responseData)


class HotelGroupChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = HotelGroup.objects.all()
    serializer_class = HotelGroupGetSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = HotelGroupPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel Grubu silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class ChilConditionThemeList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = ChilConditionThemeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ('id', 'otel',)
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = ChilConditionTheme.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = ChilConditionThemeSerializer(data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni çocuk şarı teması oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Çocuk şartı teması oluşturulamadı'
            }
        return JsonResponse(responseData)


class ChilConditionThemeChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = ChilConditionTheme.objects.all()
    serializer_class = ChilConditionThemeSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = ChilConditionThemeSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Çocuk şartı teması silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class ModulPaymentAccountInfoList(LoggingMixin, ListAPIView, CreateModelMixin):
    serializer_class = PaymentAccountInfoGetSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ('id', 'otel', )
    ordering_fields = '__all__'
    ordering = ['id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PaymentAccountInfo.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = PaymentAccountInfoPostSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            serializer.save(createdby=self.request.user,
                            updatedby=self.request.user)
            responseData = {
                'status': status.HTTP_201_CREATED,
                'message': 'Yeni otel odeme bilgisi oluşturuldu'
            }
        else:
            responseData = {
                'errors': serializer.errors,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Otel odeme bilgisi oluşturulamadı'
            }
        return JsonResponse(responseData)


class ModulPaymentAccountInfoChange(LoggingMixin, DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = PaymentAccountInfo.objects.all()
    serializer_class = PaymentAccountInfoGetSerializer
    #    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        self.serializer_class = PaymentAccountInfoPostSerializer
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedby=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.isActive:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            responseData = {
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Object Not Found'
            }
            return JsonResponse(responseData)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        responseData = {
            'status': status.HTTP_204_NO_CONTENT,
            'message': 'Otel odeme bilgisi silindi'
        }
        return JsonResponse(responseData)

    def perform_destroy(self, instance):
        instance.isActive = False
        instance.updatedby = self.request.user
        instance.save()


class EmbeddedSearchView(LoggingMixin, CreateAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = serializers.Serializer

    def post(self, request, **kwargs):

        def weekday2name(weekday):
            daylist = ["monday", "tuesday", "wednesday",
                       "thursday", "friday", "saturday", "sunday"]
            return daylist[weekday]

        def dates_bwn_twodates(start_date, end_date):
            for n in range(int((end_date - start_date).days)):
                yield start_date + timedelta(n)

        otelid = request.data["otelid"]
        keyword = request.data['keyword']
        keywords = keyword.split()
        startDate = request.data['startDate']
        finishDate = request.data['finishDate']
        if 'adultCount' in request.data.keys():
            adultCount = request.data['adultCount']
        else:
            adultCount = 0

        if 'childCount' in request.data.keys():
            childCount = request.data['childCount']
        else:
            childCount = 0

        if 'isGroupHotel' in request.data.keys():
            isGroupHotel = request.data['isGroupHotel']
        else:
            adultCount = 0
        #
        # if ('childCount' in request.data.keys()):
        #     childCount = request.data['childCount']
        # else:
        #     childCount = 0

        # adultCount = request.data['adultCount']
        # childCount = request.data['childCount']
        # params below are not active, yet!.

        # isGroupHotel = request.data['isGroupHotel']
        # firstChildren = request.data['firstChildren']
        # secondChildren = request.data['secondChildren']
        # thirdChildren = request.data['thirdChildren']
        import datetime
        date1 = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(finishDate, "%Y-%m-%d").date()
        alldateslist = [weekday2name(d.weekday())
                        for d in dates_bwn_twodates(date1, date2)]
        roomTypes = list(
            RoomType.objects.filter(otel=otelid).filter(
                reduce(operator.or_, (Q(feature__name__icontains=x) for x in keywords))).all())
        if not roomTypes:
            response = {
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Room not found"
            }
            return Response(response)
        roomList = []
        for rt in roomTypes:
            roomfeaturelist = list(
                rt.feature.values_list('name', flat=True).all())
            prices = list(PriceDetails.objects.filter(priceTemplate__roomType_id=rt.id).filter(
                accomodation__startDate__lte=startDate).filter(
                accomodation__finishDate__gte=finishDate).filter(
                adultCount__exact=adultCount).filter(childCount__exact=childCount).values().all())
            print("oda tipi id {}".format(rt))
            priceListByDays = {}
            for p in prices:
                pt = PriceTemplate.objects.get(pk=p["priceTemplate_id"])
                days = list(pt.days.values_list('id', flat=True).all())
                for d in days:
                    dayName = weekday2name(d - 1)
                    dayPrice = p[dayName + 'Price']
                    priceListByDays[dayName] = dayPrice
            totalPrice = 0
            for visitDay in alldateslist:
                totalPrice += priceListByDays.get(visitDay, 0)
            if not totalPrice == 0:
                roomObject = {
                    "roomId": rt.id,
                    "roomName": rt.name,
                    "roomFeatures": roomfeaturelist,
                    "priceList": priceListByDays,
                    "totalPrice": totalPrice
                }
                roomList.append(roomObject)
        from django.contrib.gis.geoip2 import GeoIP2
        from geoip2.errors import AddressNotFoundError
        g = GeoIP2()
        # client_ip = '46.196.152.255'
        # if not request.META. has_key('REMOTE_ADDR'):
        #     try:
        #         request.META['REMOTE_ADDR'] = request.META['HTTP_X_REAL_IP']
        #     except:
        #         request.META['REMOTE_ADDR'] = '1.1.1.1'
        #
        # client_ip = request.META['REMOTE_ADDR']
        try:
            client_ip = request.META['HTTP_X_REAL_IP']
        except:
            client_ip = '127.0.0.1'
        print(request.META['REMOTE_ADDR'])

        try:
            location = g.city(client_ip)
        except AddressNotFoundError:
            location = "No location"
        response = {
            "daysOfvisit": alldateslist,
            "client_ip": client_ip,
            "location": location,
            "roomList": roomList
        }
        return Response(response)


class MiniSearchApiView(LoggingMixin, CreateAPIView):
    serializer_class = serializers.Serializer
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):
        keyword = request.data['keyword']
        keywords = keyword.split()
        from django.db.models import CharField
        from django.db.models.functions import Lower

        CharField.register_lookup(Lower)

        byotelvalues_distinct = list(Otel.objects.filter(isActive=True, isStatusActive=True).filter(
            reduce(operator.or_, ((Q(region_text__icontains=x) | Q(location_text__icontains=x) | Q(
                region_text__icontains=x) | Q(name__icontains=x) | Q(category__name__icontains=x) | Q(
                theme__name__icontains=x)
            ) for x in
                keywords))).values_list('id', 'name', 'region_text').distinct())

        otels = []
        if byotelvalues_distinct:
            for o in byotelvalues_distinct:
                ojson = {
                    "otel_id": o[0],
                    "otel_name": o[1],
                    "region_name": o[2]
                }
                # print(ojson)
                otels.append(ojson)

        print(otels)

        # return JsonResponse({})
        return JsonResponse({"otels": otels})


class SearchApiView(LoggingMixin, CreateAPIView):
    serializer_class = serializers.Serializer
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):

        def weekday2name(weekday):
            days = ["monday", "tuesday", "wednesday",
                    "thursday", "friday", "saturday", "sunday"]
            return days[weekday]

        def dates_bwn_twodates(start_date, end_date):
            for n in range(int((end_date - start_date).days)):
                yield start_date + timedelta(n)

        def recursively_prune_dict_keys(obj, keep):
            if isinstance(obj, dict):
                return {k: recursively_prune_dict_keys(v, keep) for k, v in obj.items() if k in keep}
            elif isinstance(obj, list):
                return [recursively_prune_dict_keys(item, keep) for item in obj]
            else:
                return obj

        def sublist(lst1, lst2):
            if not lst1:
                return False
            ls1 = [element for element in lst1 if element in lst2]
            return ls1 == lst1

        def getbundledays(fromday, plus):
            retDays = []
            for d in range(fromday - 1, fromday + plus - 1):
                # print(weekday2name(d))
                retDays += [weekday2name(d)]
            return retDays

        def numOfElementsInList(listA, listB):
            """ determine number of elements of lista in listb            """
            t = 0
            for le in listA:
                if le in listB:
                    t += 1
            return t

        def daysT2E(daylist):
            daysTR = ['Pazartesi', 'Salı', 'Çarşamba',
                      'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            daysEN = ["monday", "tuesday", "wednesday",
                      "thursday", "friday", "saturday", "sunday"]
            r = []
            for d in daylist:
                r.append(daysEN[daysTR.index(d)])
            return r

        def calculateCost(fiyat, calcType, isAksiyonKademeli, hotelCommision, saleDiscount, isKickbackKademeli,
                          kickback, afiseOrani=0):
            """
            reutnr maliyet, afiseFiyati, satis fiyati, karlilik
            """
            if saleDiscount:
                saleDiscount = saleDiscount / 100
            else:
                saleDiscount = 0

            if hotelCommision:
                hotelCommision = hotelCommision / 100
            else:
                hotelCommision = 0
            if kickback:
                kickback = kickback / 100
            else:
                kickback = 0
            if afiseOrani:
                afiseOrani = afiseOrani / 100
            else:
                afiseOrani = 0
            # calcType options
            # (1, 'Net Fiyat'),
            # (2, 'Komisyonlu Fiyat'),
            maliyet = 0
            if calcType == 2:
                if isKickbackKademeli:
                    # kickback kademeli
                    if isAksiyonKademeli:
                        # aksiyon kadememi
                        maliyet = (1 - hotelCommision) * \
                            (1 - saleDiscount) * (1 - kickback) * fiyat
                        maliyet_kbsiz = (1 - hotelCommision) * \
                            (1 - saleDiscount) * fiyat

                    else:
                        # aksiyon kumulatif
                        maliyet = (1 - (hotelCommision + saleDiscount)
                                   ) * (1 - kickback) * fiyat
                        maliyet_kbsiz = (
                            1 - (hotelCommision + saleDiscount)) * fiyat
                else:
                    # kickback = kumulatif
                    if isAksiyonKademeli:
                        # aksiyon kadememi
                        maliyet = (((1 - hotelCommision) *
                                   (1 - saleDiscount)) - kickback) * fiyat
                        maliyet_kbsiz = (
                            ((1 - hotelCommision) * (1 - saleDiscount))) * fiyat

                    else:
                        # aksiyon kumulatif
                        maliyet = (
                            (1 - (hotelCommision + saleDiscount)) - kickback) * fiyat
                        maliyet_kbsiz = (
                            (1 - (hotelCommision + saleDiscount))) * fiyat

                afiseFiyat = fiyat
                satisFiyati = afiseFiyat * (1 - afiseOrani)
                if satisFiyati == 0:
                    satisFiyati = 1
                karlilik = (satisFiyati - maliyet) / satisFiyati
                kbTutari = maliyet_kbsiz - maliyet

            if calcType == 1:
                kbTutari = 0
                if isAksiyonKademeli:
                    # aksiyon kademeli
                    maliyet = fiyat * (1 - hotelCommision)
                    toplamKomisyon = (1 - (1 - hotelCommision)
                                      * (1 - saleDiscount))
                    afiseFiyat = maliyet / (1 - toplamKomisyon)
                    satisFiyati = afiseFiyat * (1 - afiseOrani)
                    karlilik = (satisFiyati - maliyet) / satisFiyati

                else:
                    # Aksiyn kumulatif
                    print(fiyat)
                    print(hotelCommision)
                    maliyet = fiyat * (1 - hotelCommision)
                    toplamKomisyon = hotelCommision + saleDiscount
                    print(toplamKomisyon)
                    print(maliyet)

                    afiseFiyat = maliyet / (1 - toplamKomisyon)
                    satisFiyati = afiseFiyat * (1 - afiseOrani)
                    print(afiseOrani)
                    print(afiseFiyat)
                    karlilik = (satisFiyati - maliyet) / satisFiyati

            return round(maliyet, 2), round(afiseFiyat, 2), round(satisFiyati, 2), round(karlilik * 100, 2), round(
                kbTutari, 2)

        keyword = request.data['keyword']
        startDate = request.data['startDate']
        finishDate = request.data['finishDate']
        print('hello dear')

        if ('otelId' in request.data.keys()):
            otelId = request.data['otelId']

        else:
            otelId = None

        if not otelId:
            print("no otel no problem")
        else:
            print("yes otel full problem")
            print(otelId)

        if ('adultCount' in request.data.keys()):
            adultCount = int(request.data['adultCount'])
        else:
            adultCount = 0

        if ('childCount' in request.data.keys()):
            childCount = int(request.data['childCount'])
        else:
            childCount = 0

        if ('advancedSearch' in request.data.keys()) and request.data['advancedSearch'] is True:
            advancedSearch = True
            advancedPriceList = []
        else:
            advancedSearch = False

        if 'childConditions' in request.data.keys():
            childConditions = request.data['childConditions']
        else:
            childConditions = []

        import datetime
        date1 = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(finishDate, "%Y-%m-%d").date()
        alldateslist = [weekday2name(d.weekday())
                        for d in dates_bwn_twodates(date1, date2)]
        if keyword != "":
            keywords = keyword.split()
        else:
            keywords = [""]
        print(keywords)
        response = {'keyword': keyword}

        if not otelId:
            byotelvalues_distinct = list(
                Otel.objects.filter(isActive=True, isStatusActive=True).filter(
                    reduce(operator.or_, ((Q(region_text__icontains=x) | Q(location_text__icontains=x) | Q(
                        region_text__icontains=x) | Q(name__icontains=x)) for x in
                        keywords))).values_list('id', flat=True).distinct())
            byfeatures_distinct = list(
                OtelFeatures.objects.filter(otel__isActive=True, otel__isStatusActive=True).filter(
                    reduce(operator.or_, (Q(feature_text__icontains=x) for x in keywords))).values_list(
                    'otel', flat=True).distinct())
            # byroomfeatures = list(PriceDetails.objects.filter(
            #     reduce(operator.or_, (Q(priceTemplate__roomType__feature__name__icontains=x) for x in keywords))
            # ).values_list('otel', flat=True).distinct())
            # print('byroomfeatures')
            # print(byroomfeatures)
            # otelslist = byfeatures_distinct + byotelvalues_distinct+byroomfeatures
            otelslist = byfeatures_distinct + byotelvalues_distinct

        else:
            otelslist = [otelId]

        otelslist = list(set(otelslist))
        response["otels"] = otelslist

        contract = Contract.objects.filter(otel_id=otelId,
                                           startDate__lte=startDate,
                                           finishDate__gte=finishDate,
                                           isActive=True).first()
        print('xxxxxxxxxxxxxxxx contract xxxxxxxxxxxxxxxxxxxxxx')
        print()
        if contract:
            response["constratComissionRate"] = contract.commissionRate
            response["constratMinPaymentRate"] = contract.minPayment
        else:
            response["constratComissionRate"] = -1
            response["constratMinPaymentRate"] = -1

        response['daysOfStay'] = alldateslist
        response["prices"] = []
        resultCount = 0
        fiyatListesi = []
        if not otelslist:
            print(' if not otelslist: ')
            response['otelsFound'] = 0
            response['pricesFound'] = 0
            return Response(response)
        for i in otelslist:
            print(' for i in otelslist: ')
            priceItem = {}
            otel = Otel.objects.get(pk=i)
            priceItem['otel_id'] = i

            if otel.name:
                priceItem['otel__name'] = otel.name
            if otel.region.name:
                priceItem['otel__region__name'] = otel.region.name
            if otel.subRegion.name:
                priceItem['otel__subRegion__name'] = otel.subRegion.name
            if otel.location:
                priceItem['otel__location__name'] = otel.location.name
            else:
                priceItem['otel__location__name'] = ""
            paf = PayAtFacility.objects.filter(
                contract__otel_id=i, isActive=True)
            if paf:
                priceItem['isPayAtFacility'] = True
            else:
                priceItem['isPayAtFacility'] = False

            priceItem['categories'] = list(
                otel.category.values_list('name', flat=True).all())
            priceItem['themes'] = list(
                otel.theme.values_list('name', flat=True).all())
            priceItem['airports'] = list(
                otel.airport.values_list('name', flat=True).all())
            otelimages = []
            try:
                images = OtelImages.objects.filter(otel_id=i, isActive=True)
            except OtelImages.DoesNotExist:
                images = None
            if images:
                otelimages = list(images.values('title', 'file').all())
            # distancesToPOIS = JSONField(null=True, blank=True)
            # extraFeatures = JSONField(null=True, blank=True)
            priceItem['distancesToPOIS'] = otel.distancesToPOIS
            priceItem['extraFeatures'] = otel.extraFeatures
            priceItem['images'] = otelimages

            # override accomodations
            accomodationsInDates = list(Accomodation.objects.filter(otel_id=i,
                                                                    startDate__lte=startDate,
                                                                    finishDate__gte=finishDate,
                                                                    isActive=True,
                                                                    isOverride=True).values_list('id',
                                                                                                 flat=True))
            print(f'Override accomodations {accomodationsInDates}')
            if len(accomodationsInDates) == 0:
                accomodationsInDates = list(Accomodation.objects.filter(otel_id=i,
                                                                        startDate__lte=startDate,
                                                                        finishDate__gte=finishDate,
                                                                        isActive=True).values_list('id',
                                                                                                   flat=True))
                print(f'Nornal accomodations {accomodationsInDates}')

            print('accomodationsInDates')
            print(accomodationsInDates)
            priceItem['accomodationsInDates'] = accomodationsInDates
            priceItem['priceItems'] = []
            # .filter(reduce(operator.or_, (Q(priceTemplate__roomType__feature__name__icontains=x) for x in keywords))
            #     priceTemplate__roomType__feature__name__icontains=keywords)

            for acs in accomodationsInDates:
                fiyatsForAcsList = []
                print('len(alldateslist) {}'.format(len(alldateslist)))
                pricesWithoutChildConditions = PriceDetails.objects.filter(
                    otel_id=i,
                    accomodation_id=acs,
                    adultCount__exact=adultCount,
                    childCount__exact=childCount,
                    minimumDays__lte=len(alldateslist),
                    isActive=True).values('id').order_by('minimumDays')
                pricesWithoutChildConditionsList = []
                print(
                    'pricesWithoutChildConditions----------------------------------------')
                print(pricesWithoutChildConditions)
                print(
                    'EOF pricesWithoutChildConditions----------------------------------------')

                for pw in pricesWithoutChildConditions:
                    print(pw['id'])
                    # print('childConds')
                    # print(childConditions)
                    pd = PriceDetails.objects.get(pk=pw['id'])
                    if childCount == 0:
                        pdekle = PriceDetails.objects.values('id',
                                                             'otel_id',
                                                             'adultCount', 'childCount', 'factor',
                                                             'currency_id',
                                                             'currency__name',
                                                             'mondayManuelPrice', 'mondayPerPersonPrice',
                                                             'mondayPrice',
                                                             'tuesdayManuelPrice', 'tuesdayPerPersonPrice',
                                                             'tuesdayPrice',
                                                             'wednesdayManuelPrice',
                                                             'wednesdayPerPersonPrice',
                                                             'wednesdayPrice',
                                                             'thursdayManuelPrice',
                                                             'thursdayPerPersonPrice',
                                                             'thursdayPrice',
                                                             'fridayManuelPrice', 'fridayPerPersonPrice',
                                                             'fridayPrice',
                                                             'saturdayManuelPrice',
                                                             'saturdayPerPersonPrice',
                                                             'saturdayPrice',
                                                             'sundayManuelPrice', 'sundayPerPersonPrice',
                                                             'sundayPrice',
                                                             'priceTemplate_id',
                                                             'minimumDays',
                                                             'maximumDays',
                                                             'factor',
                                                             'isApplyAction',
                                                             # 'accomodation_id__isBundleDays').get(pk=pw['id'])
                                                             'accomodation_id__isBundleDays').get(pk=pd.id)
                        # print(pdekle)
                        fiyatsForAcsList.append(pdekle)

                    childCondsForLoop = list(
                        pd.childCondition.values('startAge', 'finishAge').all())

                    hitCounter = 0
                    for cc in childConditions:
                        # if childCondsForLoop:

                        for ccfl in childCondsForLoop:

                            # print(' age {}'.format(cc))
                            if ccfl['startAge'] <= cc <= ccfl['finishAge']:
                                print('hit')
                                hitCounter += 1

                                # if pd.childCondition:
                                #     print(pd.childCondition.startAge)
                                print('hitCounter {}'.format(hitCounter))
                                print('childCount {}'.format(childCount))

                                if hitCounter == childCount:
                                    print(" hit bulundu {} ".format(pd.id))
                                    pdekle = PriceDetails.objects.values('id',
                                                                         'otel_id',
                                                                         'adultCount', 'childCount', 'factor',
                                                                         'currency_id',
                                                                         'currency__name',
                                                                         'mondayManuelPrice', 'mondayPerPersonPrice',
                                                                         'mondayPrice',
                                                                         'tuesdayManuelPrice', 'tuesdayPerPersonPrice',
                                                                         'tuesdayPrice',
                                                                         'wednesdayManuelPrice',
                                                                         'wednesdayPerPersonPrice',
                                                                         'wednesdayPrice',
                                                                         'thursdayManuelPrice',
                                                                         'thursdayPerPersonPrice',
                                                                         'thursdayPrice',
                                                                         'fridayManuelPrice', 'fridayPerPersonPrice',
                                                                         'fridayPrice',
                                                                         'saturdayManuelPrice',
                                                                         'saturdayPerPersonPrice',
                                                                         'saturdayPrice',
                                                                         'sundayManuelPrice', 'sundayPerPersonPrice',
                                                                         'sundayPrice',
                                                                         'priceTemplate_id',
                                                                         'minimumDays',
                                                                         'maximumDays',
                                                                         'factor',
                                                                         'isApplyAction',
                                                                         # 'accomodation_id__isBundleDays').get(pk=pw['id'])
                                                                         'accomodation_id__isBundleDays').get(pk=pd.id)
                                    # print(pdekle)
                                    fiyatsForAcsList.append(pdekle)
                                    # hitCounter=0

                fiyatsForAcs = fiyatsForAcsList
                # print(fiyatsForAcsList)
                # print(fiyatsForAcs)
                f = {}
                if fiyatsForAcs:
                    priceListByDays = {}
                    f['accomodation'] = acs
                    # f['accomodation1'] = acs
                    print(
                        ' ==================================== ++++++acs +++++++++++++++++++')
                    print(type(acs))
                    # markups = MarkUp.objects.all()

                    import time
                    markup = MarkUp.objects.filter(otel=i).filter(
                        (Q(startDate__lte=startDate) | Q(
                            startTime__lte=time.strftime('%X'))),
                        (Q(finishDate__gte=finishDate) | Q(
                            finishTime__gte=time.strftime('%X'))),
                        isActive=True).first()

                    # if markup:
                    #     print('---------markup-------')
                    #     print(markup.id)
                    #     print(markup.discountAmount)
                    #     print(markup.discountType)
                    #     f['markupAmount'] = markup.discountAmount
                    #     if markup.discountType ==1:
                    #         f['markupType'] = "Tutar"
                    #     if markup.discountType ==2:
                    #         f['markupType'] = "Yuzde"

                    mindays = []
                    pricedetails = []
                    numofelement = []

                    for facs in fiyatsForAcs:
                        isApplyAction = facs['isApplyAction']
                        print("facs['isApplyAction'] {} ".format(
                            facs['isApplyAction']))

                        print(facs['id'])
                        print(facs)
                        f['priceID'] = facs['id']
                        f['isApplyAction'] = facs['isApplyAction']

                        # print(facs['id'])
                        # pricebyid = list(PriceDetails.objects.get(pk=facs['id']).childCondition.values_list('id', flat=True).all())
                        # print(pricebyid)
                        # print(pricebyid.childCondition.values_list('id', flat=True).all())
                        pt = PriceTemplate.objects.get(
                            pk=facs['priceTemplate_id'])

                        minDays = facs['minimumDays']
                        ptDays = daysT2E(
                            list(pt.days.values_list('name', flat=True).all()))
                        numOfElements = numOfElementsInList(
                            ptDays, alldateslist)
                        mindays.append(minDays)
                        numofelement.append(numOfElements)

                        print('numOfElements {} '.format(numOfElements))
                        print('minDays {} '.format(minDays))
                        if numOfElements >= minDays:
                            print('if numOfElements >= minDays:')
                            # if numOfElementsInList(ptDays, alldateslist) == minDays:
                            pricedetails.append(pt.id)
                            ptDaysId = list(pt.days.values_list(
                                'id', flat=True).all())
                            for d in ptDaysId:
                                dayName = weekday2name(d - 1)
                                dayPrice = facs[dayName + 'Price']
                                priceListByDays[dayName] = dayPrice

                    print("priceListByDays {}".format(priceListByDays))
                    listPriceDetails = []
                    listPrice = 0
                    dayidx = 0

                    for visitDay in alldateslist:
                        print('visitDay {} '.format(visitDay))
                        listPrice += priceListByDays.get(visitDay, 0)

                        # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays.get(visitDay, 0)
                        listPriceDetails.append({
                            "date": str(date1 + timedelta(days=dayidx)),
                            "price": priceListByDays.get(visitDay, 0)
                        })
                        # nextday = str(date1 + timedelta(days=dayidx))
                        # print(str(nextday))
                        dayidx += 1

                    print("listPrice {}".format(listPrice))
                    print('listPriceDetails')
                    print(listPriceDetails)
                    # from datetime import timedelta

                    acc = Accomodation.objects.get(pk=acs)
                    ptds = PriceTemplateDetail.objects.filter(
                        adultCount=adultCount, roomType=acc.roomType.id)
                    childConds = []
                    if ptds:
                        for p in ptds:
                            print(p)
                            # print(p.childCount)
                            # print(p.factor)
                            # print(p.childCondition_text)

                            childConds.append({
                                "adultCount": p.adultCount,
                                "childCount": p.childCount,
                                "factor": p.factor,
                                "conditions": p.childCondition_text
                            })
                    # print(childConds)
                    # print(ptds)
                    # print(ptd.factor)
                    # (1, 'Net Fiyat'),
                    # (2, 'Komisyonlu Fiyat'),
                    kontenjan = Quota.objects.filter(otel=i,
                                                     quotaDate__gte=startDate,
                                                     quotaDate__lte=finishDate,
                                                     roomType=acc.roomType.id,
                                                     isActive=True
                                                     ).values_list('quotaDate', flat=True).all()
                    # print('unavailavble days')
                    # print(kontenjan)
                    if kontenjan:
                        f['isPriceAvailable'] = False
                        f['unavailableDays'] = list(kontenjan)
                    else:
                        f['isPriceAvailable'] = True
                        f['unavailableDays'] = []
                    f['childConditions'] = childConds
                    f['priceListByDays'] = priceListByDays
                    # f['numofelement'] = numofelement
                    # f['mindays'] = mindays
                    # f['pricedetails'] = pricedetails
                    # print(acc.currency.name)
                    f['accomodation__childFreeStatus'] = acc.childFreeStatus
                    f['accomodation__roomType'] = acc.roomType.id
                    f['accomodation__roomType__name'] = acc.roomType.name
                    f['accomodation__roomType__description'] = acc.roomType.description
                    f['accomodation__roomType__roomSize'] = acc.roomType.roomSize
                    f['accomodation__roomType__guestCount'] = acc.roomType.guestCount
                    f['accomodation__roomType__bedCapacity'] = acc.roomType.bedCapacity
                    # odaResimleri = OtelImages.objects.filter(roomType=acc.roomType.id)
                    # print('odaResimleri')
                    # print(odaResimleri)

                    odaResimleriDefault = []
                    try:
                        odaImagesDefault = OtelImages.objects.filter(
                            roomType=acc.roomType.id, isDefault=True)
                        # odaImages = OtelImages.objects.filter(roomType=112)
                    except OtelImages.DoesNotExist:
                        odaImagesDefault = None

                    if odaImagesDefault:
                        odaResimleriDefault = list(
                            odaImagesDefault.values('title', 'file').all())

                    f['accomodation__roomType__images_default'] = odaResimleriDefault

                    odaResimleri = []
                    try:
                        odaImages = OtelImages.objects.filter(
                            roomType=acc.roomType.id, isDefault=False)
                        # odaImages = OtelImages.objects.filter(roomType=112)
                    except OtelImages.DoesNotExist:
                        odaImages = None

                    if odaImages:
                        odaResimleri = list(
                            odaImages.values('title', 'file').all())

                    f['accomodation__roomType__images'] = odaResimleri

                    f['accomodation__pensionType'] = acc.concept.id
                    f['accomodation__pensionType__name'] = acc.concept.name
                    f['currency_id'] = acc.currency.id
                    f['currency_name'] = acc.currency.name
                    f['priceFactor'] = facs['factor']
                    f['roomFeatures'] = list(
                        acc.roomType.feature.values_list('name', flat=True).all())
                    # print(acc.roomType.name)
                    # print(type(acc.roomType.roomSize))
                    calcType = acc.priceCalcType
                    # print(acc.priceCalcType)
                    kickbackInDates = KickBack.objects.filter(otel_id=i, startDate__lte=startDate,
                                                              finishDate__gte=finishDate,
                                                              isActive=True).values('id',
                                                                                    'amount',
                                                                                    'isKademeliKumulatif').first()
                    print('kickbackInDates')
                    print(kickbackInDates)
                    if kickbackInDates:
                        # print(kickbackInDates['amount'])
                        # print(kickbackInDates['isKademeliKumulatif'])
                        kickbackAmount = kickbackInDates['amount']
                        isKickbackKademeli = kickbackInDates['isKademeliKumulatif']
                    else:
                        kickbackAmount = 0
                        isKickbackKademeli = False
                    # genel aksiyon var mi?
                    actionsInDates = ActionsDetail.objects.filter(
                        (Q(isApplyAllRoomTypes=True) | Q(
                            roomType__in=[f['accomodation__roomType']])),
                        # (Q(actions__id=2) & ~Q(totalDays__lte=len(alldateslist))),
                        (Q(actions__id=1)),
                        otel_id=i,
                        # startDate__lte=startDate,
                        # finishDate__gte=finishDate,
                        salesStartDate__lte=startDate,
                        salesFinishDate__gte=finishDate,
                        isActive=True).values(
                        # (isApplyAllRoomTypes=True) or (roomType=f['accomodation__roomType'])).values(
                        'id', 'name', 'hotelCommission', 'saleDiscount', 'isKademeli', 'fakeRate',
                        'discountRate', 'actions__name', 'actions_id',
                        'isApplyAllRoomTypes', 'roomType',
                        'dayActionCalculation', 'totalDays', 'paidDays', 'minKonaklama', 'webDescription').all().distinct('id',
                                                                                                                          'actions_id').order_by(
                        'actions_id')
                    # once sartlari uymayan gun aksiyonlarini cikartalim
                    # actionsInDates = actionsInDates.exclude(
                    #     (Q(actions__id=2) & ~Q(minKonaklama__lte=len(alldateslist))))
                    # actionsInDates = actionsInDates.exclude(Q(actions=2))
                    # print('actionsInDates')
                    # print(actionsInDates)

                    f['listPrice'] = listPrice
                    print('listPrice')
                    print(listPrice)

                    e = ExtraServices.objects.filter(serviceType=1, otel__in=[i]).filter(
                        Q(lowerLimit__lte=listPrice) & Q(upperLimit__gte=listPrice)).values('price').first()
                    # print('d22-----------------------------------')
                    # print(e['price'])
                    if e != None:
                        f['cancelInsuranceAmount'] = e['price']
                    else:
                        f['cancelInsuranceAmount'] = -1
                    priceListByDays_updated = {}

                    maliyet = listPrice
                    print('listPrice')
                    print(listPrice)
                    actionsApplied = []
                    if actionsInDates:
                        actionInDate = actionsInDates.first()
                        print('actionInDate')
                        print(actionInDate)
                        otherActions = ActionsDetail.objects.get(pk=actionInDate['id']).otherAction.filter(
                            salesStartDate__lte=startDate,
                            salesFinishDate__gte=finishDate,
                            isActive=True,
                            isStatusActive=True).values(
                            'id',
                            'name',
                            'hotelCommission',
                            'saleDiscount',
                            'isKademeli',
                            'fakeRate',
                            'discountRate',
                            'actions__name',
                            'actions_id',
                            'isApplyAllRoomTypes',
                            'roomType',
                            'dayActionCalculation',
                            'totalDays',
                            'paidDays',
                            'minKonaklama',
                            'webDescription').all().distinct('id',  'actions_id')
                        # 'webDescription').all().distinct('id', 'actions_id')
                        print('      otherActions      ')
                        print(otherActions)
                        otherActions = otherActions.exclude(
                            (
                                Q(actions__id=2) & ~(
                                    Q(minKonaklama__lte=len(alldateslist)) & Q(
                                        maxKonaklama__gte=len(alldateslist))
                                )
                            )
                        )

                        # otherActions = otherActions.exclude(
                        #     (Q(actions__id=2) & ~Q(minKonaklama__lte=len(alldateslist))))

                        # print(otherActions.count())
                        # print(otherActions)

                        # otherActions = actionInDate.otherAction.objects.all()
                        # print(actionInDate)
                        hotelCommision = actionInDate['hotelCommission']
                        saleDiscount = actionInDate['saleDiscount']
                        discountRate = actionInDate['discountRate']
                        isAksiyonKademeli = actionInDate['isKademeli']
                        kickbackDiscountAmount = 0
                        if not otherActions:
                            # Eger bagli alt aksiyon yoksa
                            maliyet_old = maliyet
                            print('maliyet')
                            print(maliyet)
                            maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                maliyet, calcType,
                                isAksiyonKademeli,
                                hotelCommision, discountRate,
                                isKickbackKademeli,
                                kickbackAmount, saleDiscount)
                            for key, value in priceListByDays.items():
                                value_updated, _, _, _, _ = calculateCost(
                                    value, calcType,
                                    isAksiyonKademeli,
                                    hotelCommision, discountRate,
                                    isKickbackKademeli,
                                    0, saleDiscount)
                                priceListByDays_updated[key] = value_updated
                            priceListByDays_updated = dict(
                                sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                       reverse=False))
                            print(" maliyet, afiseFiyat, satisFiyati, karlilik")
                            print(" {:2f}       {:2f}          {:2f}           {:2f} ".format(maliyet, afiseFiyat,
                                                                                              satisFiyati, karlilik))
                            # if markup:
                            #     1 tutar 2 yuzde
                            #     if markup.discountType == 2:
                            #         satisFiyati = satisFiyati * (100 - markup.discountAmount)/100
                            #     if markup.discountType == 1:
                            #         satisFiyati = satisFiyati - markup.discountAmount

                            f['maliyet'] = maliyet
                            f['afiseFiyat'] = afiseFiyat
                            f['satisFiyati'] = satisFiyati
                            f['karlilik'] = karlilik
                            f['kickbackTutari'] = kbTutari
                            # maliyet, afiseFiyat, satisFiyati, karlilik)

                            # print(" {} {} {} {} ".format(maliyet, afiseFiyat, satisFiyati,
                            #                              karlilik))

                            actionsApplied.append({
                                "action_id": actionInDate['id'],
                                "action_name": actionInDate['actions__name'],
                                "action_name_full": actionInDate['name'],
                                "actionWebDescription": actionInDate['webDescription'],
                                "listPrice": listPrice,
                                "maliyet": maliyet,
                                "afiseFiyat": afiseFiyat,
                                "satisFiyati": satisFiyati,
                                "karlilik": karlilik,
                                "aksiyonIndirimTutari": maliyet_old - maliyet,
                                "aksiyonluFiyatListesi": priceListByDays_updated
                            })
                            listPriceDetails = []
                            dayidx = 0
                            for visitDay in alldateslist:
                                # listPrice += priceListByDays_updated.get(visitDay, 0)

                                # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                                # listPriceDetails.append({
                                #     str(date1 + timedelta(days=dayidx)): priceListByDays_updated.get(visitDay, 0)
                                # })
                                listPriceDetails.append({
                                    "date": str(date1 + timedelta(days=dayidx)),
                                    "price": priceListByDays.get(visitDay, 0)
                                })
                                dayidx += 1

                            print(listPriceDetails)

                        else:
                            print('# Eger bagli alt aksiyon(lar) VARSA')

                            print('isApplyAction == {}'.format(isApplyAction))
                            print("f['isApplyAction'] {} ".format(
                                f['isApplyAction']))

                        # elif isApplyAction:
                            if isApplyAction:
                                print('alt aksion uygulaniyor')

                                for oa in otherActions:
                                    print(oa)
                                maliyet_old = maliyet
                                maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                    maliyet, calcType,
                                    isAksiyonKademeli,
                                    hotelCommision, discountRate,
                                    isKickbackKademeli,
                                    0, saleDiscount)
                                for key, value in priceListByDays.items():
                                    _, _, value_updated, _, _ = calculateCost(
                                        value, calcType,
                                        isAksiyonKademeli,
                                        hotelCommision, discountRate,
                                        isKickbackKademeli,
                                        0, saleDiscount)
                                    priceListByDays_updated[key] = value_updated
                                    # priceListByDays_updated.append(key+'_': value_updated)
                                priceListByDays_updated = dict(
                                    sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                           reverse=False))
                                # print(priceListByDays_updated)
                                print(" maliyet, afiseFiyat, satisFiyati, karlilik")
                                print(" {:2f}       {:2f}          {:2f}           {:2f} ".format(maliyet, afiseFiyat,
                                                                                                  satisFiyati,
                                                                                                  karlilik))
                                listPriceDetails = []
                                dayidx = 0
                                for visitDay in alldateslist:
                                    # listPrice += priceListByDays_updated.get(visitDay, 0)

                                    # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                                    # listPriceDetails.append({
                                    #     str(date1 + timedelta(days=dayidx)):
                                    #     priceListByDays_updated.get(visitDay, 0)
                                    # })
                                    listPriceDetails.append({
                                        "date": str(date1 + timedelta(days=dayidx)),
                                        "price": priceListByDays_updated.get(visitDay, 0)
                                    })
                                    dayidx += 1

                                print(listPriceDetails)
                                if markup:
                                    print(" markup sar")
                                    # 1 tutar 2 yuzde
                                    if markup.discountType == 2:
                                        satisFiyati = satisFiyati * \
                                            (100 - markup.discountAmount) / 100
                                    if markup.discountType == 1:
                                        satisFiyati = satisFiyati - markup.discountAmount

                                f['maliyet'] = maliyet
                                f['afiseFiyat'] = afiseFiyat
                                f['satisFiyati'] = satisFiyati
                                f['karlilik'] = karlilik
                                f['kickbackTutari'] = kbTutari

                                # maliyet, afiseFiyat, satisFiyati, karlilik)

                                # print(" {} {} {} {} ".format(maliyet, afiseFiyat, satisFiyati,
                                #                              karlilik))
                                actionsApplied.append({
                                    "action_id": actionInDate['id'],
                                    "action_name": actionInDate['actions__name'],
                                    "action_name_full": actionInDate['name'],
                                    "actionWebDescription": actionInDate['webDescription'],
                                    "listPrice": listPrice,
                                    "maliyet": maliyet,
                                    "afiseFiyat": afiseFiyat,
                                    "satisFiyati": satisFiyati,
                                    "karlilik": karlilik,
                                    "aksiyonIndirimTutari": maliyet_old - maliyet,
                                    "aksiyonluFiyatListesi": priceListByDays_updated
                                })
                                actionslist_len = len(otherActions)
                                for index, acid in enumerate(otherActions):
                                    print('actions_id')
                                    print(acid['actions_id'])
                                    if acid['actions_id'] == 2:
                                        # gun aksyionu
                                        # unpaidDays = acid['minKonaklama'] - acid['paidDays']
                                        unpaidDays = acid['paidDays']
                                        discountAmount = unpaidDays * \
                                            (list(
                                                priceListByDays_updated.values())[0])
                                        # discountCost = unpaidDays * (list(priceListByDays.values())[0])
                                        print("Gun aksyionu uygulaniyor [Indirim tutari= {}]".format(
                                            discountAmount))
                                        maliyet_old = maliyet
                                        maliyet -= unpaidDays * \
                                            (maliyet / len(alldateslist))
                                        # maliyet -= discountCost
                                        # afiseFiyat -= discountAmount
                                        satisFiyati -= discountAmount

                                        # if index == actionslist_len - 1:
                                        #     maliyet_old = maliyet
                                        #     maliyet = maliyet * (1 - kickbackAmount / 100)
                                        #     afiseFiyat = afiseFiyat * (1 - kickbackAmount / 100)
                                        #     satisFiyati = satisFiyati * (1 - kickbackAmount / 100)
                                        #     print(' KICKback uygulandi {:2f}'.format(kickbackAmount))

                                        karlilik = (
                                            satisFiyati - maliyet) / satisFiyati
                                        # karlilik = (satisFiyati - maliyet) /

                                        maliyet = round(maliyet, 2)
                                        afiseFiyat = round(afiseFiyat, 2)
                                        satisFiyati = round(satisFiyati, 2)
                                        karlilik = round(karlilik * 100, 2)
                                        # f['kickbackAmount'] = maliyet_old - maliyet

                                        listPriceDetails = []
                                        dayidx = 0
                                        for visitDay in alldateslist:
                                            # listPrice += priceListByDays_updated.get(visitDay, 0)

                                            if dayidx <= len(alldateslist) - unpaidDays-1:
                                                # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                                                #
                                                # listPriceDetails.append({
                                                #     str(date1 + timedelta(days=dayidx)): priceListByDays_updated.get(visitDay, 0)
                                                # })
                                                listPriceDetails.append({
                                                    "date": str(date1 + timedelta(days=dayidx)),
                                                    "price": priceListByDays_updated.get(visitDay, 0)
                                                })
                                            else:
                                                # listPriceDetails[str(date1 + timedelta(days=dayidx))] = 0
                                                # listPriceDetails.append({
                                                #     str(date1 + timedelta(days=dayidx)): 0})

                                                listPriceDetails.append({
                                                    "date": str(date1 + timedelta(days=dayidx)),
                                                    "price": 0
                                                })
                                            dayidx += 1

                                        print(listPriceDetails)

                                    if acid['actions_id'] in [3, 4, 5, 6]:
                                        print('Genel aksiyon uygulandi..')
                                        hotelCommision = acid['hotelCommission']
                                        saleDiscount = acid['saleDiscount']
                                        discountRate = acid['discountRate']
                                        isAksiyonKademeli = acid['isKademeli']

                                        if index == actionslist_len - 1:
                                            print('son aksiyon')
                                            maliyet_old = maliyet
                                            maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                                maliyet, calcType,
                                                isAksiyonKademeli,
                                                hotelCommision, discountRate,
                                                isKickbackKademeli,
                                                kickbackAmount, saleDiscount)

                                            f['kickbackAmount'] = maliyet_old - maliyet
                                            for key, value in priceListByDays.items():
                                                value_updated, _, _, _, _ = calculateCost(
                                                    value, calcType,
                                                    isAksiyonKademeli,
                                                    hotelCommision, discountRate,
                                                    isKickbackKademeli,
                                                    0, saleDiscount)
                                                priceListByDays_updated[key] = value_updated
                                            priceListByDays_updated = dict(
                                                sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                                       reverse=False))
                                            listPriceDetails = []
                                            dayidx = 0
                                            for visitDay in alldateslist:
                                                # listPrice += priceListByDays_updated.get(visitDay, 0)

                                                # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(
                                                #     visitDay, 0)
                                                # listPriceDetails.append({
                                                #     str(date1 + timedelta(days=dayidx)): priceListByDays_updated.get(
                                                #         visitDay, 0)
                                                # })
                                                listPriceDetails.append({
                                                    "date": str(date1 + timedelta(days=dayidx)),
                                                    "price": priceListByDays_updated.get(visitDay, 0)
                                                })
                                                dayidx += 1

                                            print(listPriceDetails)
                                        else:
                                            maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                                maliyet, calcType,
                                                isAksiyonKademeli,
                                                hotelCommision, discountRate,
                                                isKickbackKademeli,
                                                0, saleDiscount)
                                            for key, value in priceListByDays.items():
                                                value_updated, _, _, _, kbTutari = calculateCost(
                                                    value, calcType,
                                                    isAksiyonKademeli,
                                                    hotelCommision, discountRate,
                                                    isKickbackKademeli,
                                                    0, saleDiscount)
                                                priceListByDays_updated[key] = value_updated
                                                # priceListByDays_updated.append(key+'_': value_updated)
                                            priceListByDays_updated = dict(
                                                sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                                       reverse=False))
                                    if markup:
                                        # 1 tutar 2 yuzde
                                        if markup.discountType == 2:
                                            satisFiyati = satisFiyati * \
                                                (100 - markup.discountAmount) / 100
                                        if markup.discountType == 1:
                                            satisFiyati = satisFiyati - markup.discountAmount
                                    actionsApplied.append({
                                        "action_id": acid['id'],
                                        "action_name": acid['actions__name'],
                                        "action_name_full": acid['name'],
                                        "actionWebDescription": acid['webDescription'],
                                        "listPrice": listPrice,
                                        "maliyet": maliyet,
                                        "afiseFiyat": afiseFiyat,
                                        "satisFiyati": satisFiyati,
                                        "karlilik": karlilik,
                                        "aksiyonIndirimTutari": maliyet_old - maliyet,
                                        "aksiyonluFiyatListesi": priceListByDays_updated
                                    })
                                    f['maliyet'] = maliyet
                                    f['afiseFiyat'] = afiseFiyat
                                    f['satisFiyati'] = satisFiyati
                                    f['karlilik'] = karlilik
                                    f['kickbackTutari'] = kbTutari

                                # print('actionslist_len')
                                # print(actionslist_len)
                                #
                                # for oa in otherActions:
                                #     print(oa)
                            else:
                                print('alt aksiyon uygulanmadi')
                                for oa in otherActions:
                                    print(oa)
                                maliyet_old = maliyet
                                maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                    maliyet, calcType,
                                    isAksiyonKademeli,
                                    hotelCommision, discountRate,
                                    isKickbackKademeli,
                                    0, saleDiscount)
                                for key, value in priceListByDays.items():
                                    value_updated, _, _, _, _ = calculateCost(
                                        value, calcType,
                                        isAksiyonKademeli,
                                        hotelCommision, discountRate,
                                        isKickbackKademeli,
                                        0, saleDiscount)
                                    priceListByDays_updated[key] = value_updated
                                    # priceListByDays_updated.append(key+'_': value_updated)
                                priceListByDays_updated = dict(
                                    sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                           reverse=False))
                                # print(priceListByDays_updated)
                                print(" maliyet, afiseFiyat, satisFiyati, karlilik")
                                print(" {:2f}       {:2f}          {:2f}           {:2f} ".format(maliyet, afiseFiyat,
                                                                                                  satisFiyati,
                                                                                                  karlilik))
                                listPriceDetails = []
                                dayidx = 0
                                for visitDay in alldateslist:
                                    # listPrice += priceListByDays_updated.get(visitDay, 0)

                                    # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                                    # listPriceDetails.append({
                                    #     str(date1 + timedelta(days=dayidx)):
                                    #     priceListByDays_updated.get(visitDay, 0)
                                    # })
                                    listPriceDetails.append({
                                        "date": str(date1 + timedelta(days=dayidx)),
                                        "price": priceListByDays_updated.get(visitDay, 0)
                                    })
                                    dayidx += 1

                                print(listPriceDetails)
                                if markup:
                                    # 1 tutar 2 yuzde
                                    if markup.discountType == 2:
                                        satisFiyati = satisFiyati * \
                                            (100 - markup.discountAmount) / 100
                                    if markup.discountType == 1:
                                        satisFiyati = satisFiyati - markup.discountAmount

                                f['maliyet'] = maliyet
                                f['afiseFiyat'] = afiseFiyat
                                f['satisFiyati'] = satisFiyati
                                f['karlilik'] = karlilik
                                f['kickbackTutari'] = kbTutari

                                # maliyet, afiseFiyat, satisFiyati, karlilik)

                                # print(" {} {} {} {} ".format(maliyet, afiseFiyat, satisFiyati,
                                #                              karlilik))
                                actionsApplied.append({
                                    "action_id": actionInDate['id'],
                                    "action_name": actionInDate['actions__name'],
                                    "action_name_full": actionInDate['name'],
                                    "actionWebDescription": actionInDate['webDescription'],
                                    "listPrice": listPrice,
                                    "maliyet": maliyet,
                                    "afiseFiyat": afiseFiyat,
                                    "satisFiyati": satisFiyati,
                                    "karlilik": karlilik,
                                    "aksiyonIndirimTutari": maliyet_old - maliyet,
                                    "aksiyonluFiyatListesi": priceListByDays_updated
                                })

                    else:
                        print('no actions get contract')
                        c = Contract.objects.filter(otel_id=i, startDate__lte=startDate,
                                                    finishDate__gte=finishDate,
                                                    isActive=True).values('id',
                                                                          'commissionRate').order_by(
                            'id').last()
                        print(c)

                        f['acc_id'] = 0
                        f['maliyet'] = 0
                        f['afiseFiyat'] = 0
                        f['satisFiyati'] = 0
                        f['karlilik'] = 0
                    f['listPriceDetails'] = listPriceDetails
                    f['actionsApplied'] = actionsApplied
                    # print(f)

                if f:
                    priceItem['priceItems'].append(f)
                    resultCount += 1
            if len(priceItem['priceItems']) > 0:
                response["prices"].append(priceItem)
        response['otelsFound'] = len(response["prices"])
        response['pricesFound'] = resultCount

        if resultCount > 0:
            searchKeyword = request.data['keyword']
            searchStartDate = request.data['startDate']
            searchFinishDate = request.data['finishDate']
            if ('otelId' in request.data.keys()):
                searchOtelId = request.data['otelId']
            else:
                searchOtelId = None
            searchChildCondition = request.data['childConditions']
            searchAdultCount = int(request.data['adultCount'])
            searchChildCount = int(request.data['childCount'])
            searchFoundOtelIds = response['otelsFound']
            searchFoundPrices = response["prices"]
            searchResultCount = resultCount
            print(' ----      searchFoundPrices     ------------')

            searchStartDate = datetime.datetime.strptime(
                searchStartDate, "%Y-%m-%d")
            searchFinishDate = datetime.datetime.strptime(
                searchFinishDate, "%Y-%m-%d")
            print(searchStartDate)
            import json
            serialized_obj = json.dumps(
                searchFoundPrices, cls=DjangoJSONEncoder)
            s = SearchLog.objects.create(
                otel_id=searchOtelId,
                keywords=searchKeyword,
                startDate=searchStartDate,
                finishDate=searchFinishDate,
                childCondition=searchChildCondition,
                adultCount=searchAdultCount,
                childCount=searchChildCount,
                pricesFound=searchResultCount,
                otelsFound=searchFoundOtelIds,
                # response=json.loads(json.dumps(searchFoundPrices))
                response=serialized_obj
            )
            if s:
                response['searchID'] = s.id

        return Response(response)


class SearchApiViewUpated(LoggingMixin, CreateAPIView):
    serializer_class = serializers.Serializer
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):

        def weekday2name(weekday):
            days = ["monday", "tuesday", "wednesday",
                    "thursday", "friday", "saturday", "sunday"]
            return days[weekday]

        def dates_bwn_twodates(start_date, end_date):
            for n in range(int((end_date - start_date).days)):
                yield start_date + timedelta(n)

        def recursively_prune_dict_keys(obj, keep):
            if isinstance(obj, dict):
                return {k: recursively_prune_dict_keys(v, keep) for k, v in obj.items() if k in keep}
            elif isinstance(obj, list):
                return [recursively_prune_dict_keys(item, keep) for item in obj]
            else:
                return obj

        def sublist(lst1, lst2):
            if not lst1:
                return False
            ls1 = [element for element in lst1 if element in lst2]
            return ls1 == lst1

        def getbundledays(fromday, plus):
            retDays = []
            for d in range(fromday - 1, fromday + plus - 1):
                # print(weekday2name(d))
                retDays += [weekday2name(d)]
            return retDays

        def numOfElementsInList(listA, listB):
            """ determine number of elements of lista in listb            """
            t = 0
            for le in listA:
                if le in listB:
                    t += 1
            return t

        def daysT2E(daylist):
            daysTR = ['Pazartesi', 'Salı', 'Çarşamba',
                      'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            daysEN = ["monday", "tuesday", "wednesday",
                      "thursday", "friday", "saturday", "sunday"]
            r = []
            for d in daylist:
                r.append(daysEN[daysTR.index(d)])
            return r

        def calculateCost(fiyat, calcType, isAksiyonKademeli, hotelCommision, saleDiscount, isKickbackKademeli,
                          kickback, afiseOrani=0):
            """
            reutnr maliyet, afiseFiyati, satis fiyati, karlilik
            """
            if saleDiscount:
                saleDiscount = saleDiscount / 100
            else:
                saleDiscount = 0

            if hotelCommision:
                hotelCommision = hotelCommision / 100
            else:
                hotelCommision = 0
            if kickback:
                kickback = kickback / 100
            else:
                kickback = 0
            if afiseOrani:
                afiseOrani = afiseOrani / 100
            else:
                afiseOrani = 0
            # calcType options
            # (1, 'Net Fiyat'),
            # (2, 'Komisyonlu Fiyat'),
            maliyet = 0
            if calcType == 2:
                if isKickbackKademeli:
                    # kickback kademeli
                    if isAksiyonKademeli:
                        # aksiyon kadememi
                        maliyet = (1 - hotelCommision) * \
                            (1 - saleDiscount) * (1 - kickback) * fiyat
                        maliyet_kbsiz = (1 - hotelCommision) * \
                            (1 - saleDiscount) * fiyat

                    else:
                        # aksiyon kumulatif
                        maliyet = (1 - (hotelCommision + saleDiscount)
                                   ) * (1 - kickback) * fiyat
                        maliyet_kbsiz = (
                            1 - (hotelCommision + saleDiscount)) * fiyat
                else:
                    # kickback = kumulatif
                    if isAksiyonKademeli:
                        # aksiyon kadememi
                        maliyet = (((1 - hotelCommision) *
                                   (1 - saleDiscount)) - kickback) * fiyat
                        maliyet_kbsiz = (
                            ((1 - hotelCommision) * (1 - saleDiscount))) * fiyat

                    else:
                        # aksiyon kumulatif
                        maliyet = (
                            (1 - (hotelCommision + saleDiscount)) - kickback) * fiyat
                        maliyet_kbsiz = (
                            (1 - (hotelCommision + saleDiscount))) * fiyat

                afiseFiyat = fiyat
                satisFiyati = afiseFiyat * (1 - afiseOrani)
                if satisFiyati == 0:
                    satisFiyati = 1
                karlilik = (satisFiyati - maliyet) / satisFiyati
                kbTutari = maliyet_kbsiz - maliyet

            if calcType == 1:
                kbTutari = 0
                if isAksiyonKademeli:
                    # aksiyon kademeli
                    maliyet = fiyat * (1 - hotelCommision)
                    toplamKomisyon = (1 - (1 - hotelCommision)
                                      * (1 - saleDiscount))
                    afiseFiyat = maliyet / (1 - toplamKomisyon)
                    satisFiyati = afiseFiyat * (1 - afiseOrani)
                    karlilik = (satisFiyati - maliyet) / satisFiyati

                else:
                    # Aksiyn kumulatif
                    maliyet = fiyat * (1 - hotelCommision)
                    toplamKomisyon = hotelCommision + saleDiscount
                    afiseFiyat = maliyet / (1 - toplamKomisyon)
                    satisFiyati = afiseFiyat * (1 - afiseOrani)
                    karlilik = (satisFiyati - maliyet) / satisFiyati

            return round(maliyet, 2), round(afiseFiyat, 2), round(satisFiyati, 2), round(karlilik * 100, 2), round(
                kbTutari, 2)

        keyword = request.data['keyword']
        startDate = request.data['startDate']
        finishDate = request.data['finishDate']

        if ('otelId' in request.data.keys()):
            otelId = request.data['otelId']

        else:
            otelId = None

        if not otelId:
            print("no otel no problem")
        else:
            print("yes otel full problem")
            print(otelId)

        if ('adultCount' in request.data.keys()):
            adultCount = int(request.data['adultCount'])
        else:
            adultCount = 0

        if ('childCount' in request.data.keys()):
            childCount = int(request.data['childCount'])
        else:
            childCount = 0

        if ('advancedSearch' in request.data.keys()) and request.data['advancedSearch'] is True:
            advancedSearch = True
            advancedPriceList = []
        else:
            advancedSearch = False

        if 'childConditions' in request.data.keys():
            childConditions = request.data['childConditions']
        else:
            childConditions = []

        import datetime
        date1 = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(finishDate, "%Y-%m-%d").date()
        alldateslist = [weekday2name(d.weekday())
                        for d in dates_bwn_twodates(date1, date2)]
        if keyword != "":
            keywords = keyword.split()
        else:
            keywords = [""]
        print(keywords)
        response = {'keyword': keyword}

        if not otelId:
            byotelvalues_distinct = list(
                Otel.objects.filter(isActive=True, isStatusActive=True).filter(
                    reduce(operator.or_, ((Q(region_text__icontains=x) | Q(location_text__icontains=x) | Q(
                        region_text__icontains=x) | Q(name__icontains=x)) for x in
                        keywords))).values_list('id', flat=True).distinct())
            byfeatures_distinct = list(
                OtelFeatures.objects.filter(otel__isActive=True, otel__isStatusActive=True).filter(
                    reduce(operator.or_, (Q(feature_text__icontains=x) for x in keywords))).values_list(
                    'otel', flat=True).distinct())
            # byroomfeatures = list(PriceDetails.objects.filter(
            #     reduce(operator.or_, (Q(priceTemplate__roomType__feature__name__icontains=x) for x in keywords))
            # ).values_list('otel', flat=True).distinct())
            # print('byroomfeatures')
            # print(byroomfeatures)
            # otelslist = byfeatures_distinct + byotelvalues_distinct+byroomfeatures
            otelslist = byfeatures_distinct + byotelvalues_distinct

        else:
            otelslist = [otelId]

        otelslist = list(set(otelslist))
        response["otels"] = otelslist

        contract = Contract.objects.filter(otel_id=otelId,
                                           startDate__lte=startDate,
                                           finishDate__gte=finishDate,
                                           isActive=True).first()
        print('xxxxxxxxxxxxxxxx contract xxxxxxxxxxxxxxxxxxxxxx')
        print()
        if contract:
            response["constratComissionRate"] = contract.commissionRate
        else:
            response["constratComissionRate"] = -1

        response['daysOfStay'] = alldateslist
        response["prices"] = []
        resultCount = 0
        fiyatListesi = []
        if not otelslist:
            response['otelsFound'] = 0
            response['pricesFound'] = 0
            return Response(response)
        for i in otelslist:
            priceItem = {}
            otel = Otel.objects.get(pk=i)
            priceItem['otel_id'] = i
            if otel.name:
                priceItem['otel__name'] = otel.name
            if otel.region.name:
                priceItem['otel__region__name'] = otel.region.name
            if otel.subRegion.name:
                priceItem['otel__subRegion__name'] = otel.subRegion.name
            if otel.location:
                priceItem['otel__location__name'] = otel.location.name
            else:
                priceItem['otel__location__name'] = ""
            priceItem['categories'] = list(
                otel.category.values_list('name', flat=True).all())
            priceItem['themes'] = list(
                otel.theme.values_list('name', flat=True).all())
            priceItem['airports'] = list(
                otel.airport.values_list('name', flat=True).all())
            otelimages = []
            try:
                images = OtelImages.objects.filter(otel_id=i, isActive=True)
            except OtelImages.DoesNotExist:
                images = None
            if images:
                otelimages = list(images.values('title', 'file').all())
            priceItem['images'] = otelimages
            print(startDate)
            print(finishDate)
            # multiAccomodationsInDates = Accomodation.objects.filter(otel_id=i).filter(
            #     # startDate__range=[startDate, finishDate],
            #     (Q(startDate__lte=startDate) & Q(finishDate__gte=startDate)) |
            #     (Q(startDate__lte=finishDate) & Q(finishDate__gte=finishDate)),
            #     # (Q(startDate__lte=finishDate) & Q(finishDate__gte=finishDate)),
            #     isActive=True)
            multiAccomodationsInDates = Accomodation.objects.filter(otel_id=i).filter(
                ((Q(startDate__lte=startDate) & Q(finishDate__gte=startDate))
                 & ~(Q(startDate__lte=finishDate) & Q(finishDate__gte=finishDate))),
                isActive=True)
            print('multiAccomodationsInDates')
            print(multiAccomodationsInDates)
            singleSpanAccIDs = []
            multiSpanAccIDGroups = []
            for mad in multiAccomodationsInDates:
                nextAccomodationsInDates = Accomodation.objects.filter(otel_id=mad.otel_id).filter(
                    (~(Q(startDate__lte=startDate) & Q(finishDate__gte=startDate))
                     & (Q(startDate__lte=finishDate) & Q(finishDate__gte=finishDate))),
                    isActive=True, roomType_id=mad.roomType.id).first()
                if nextAccomodationsInDates:
                    multiSpanAccIDGroups.append(
                        [mad.id, nextAccomodationsInDates.id])

            print(singleSpanAccIDs)

            if multiSpanAccIDGroups:
                print(multiSpanAccIDGroups)
                priceItem['multiSpanAccIDGroups'] = multiSpanAccIDGroups
                for msAccId in multiSpanAccIDGroups:
                    print(msAccId[0])
                    msFirstPricesWithoutChildConditions = PriceDetails.objects.filter(
                        otel_id=i,
                        accomodation_id=msAccId[0],
                        adultCount__exact=adultCount,
                        childCount__exact=childCount,
                        isActive=True).values(
                        # 'id',
                        #   'otel_id',
                        #   'adultCount', 'childCount', 'factor',
                        #   'currency_id',
                        #   'currency__name',
                        #   'mondayPrice',
                        #   'tuesdayPrice',
                        #   'wednesdayPrice',
                        #   'thursdayPrice',
                        #   'fridayPrice',
                        #   'saturdayPrice',
                        #   'sundayPrice',
                        #   'priceTemplate_id',
                        #   'minimumDays',
                        #   'maximumDays',
                        #   'factor',
                        #   'accomodation__startDate',
                        #   'accomodation__finishDate',
                        #   'priceTemplate_id'
                    ).order_by('minimumDays')
                    if msFirstPricesWithoutChildConditions:
                        for msfp in msFirstPricesWithoutChildConditions:
                            print(msfp)

                    msLastPricesWithoutChildConditions = PriceDetails.objects.filter(
                        otel_id=i,
                        accomodation_id=msAccId[1],
                        adultCount__exact=adultCount,
                        childCount__exact=childCount,
                        isActive=True).values(
                        # 'id',
                        #  'otel_id',
                        #  'adultCount', 'childCount', 'factor',
                        #  'currency_id',
                        #  'currency__name',
                        #  'mondayPrice',
                        #  'tuesdayPrice',
                        #  'wednesdayPrice',
                        #  'thursdayPrice',
                        #  'fridayPrice',
                        #  'saturdayPrice',
                        #  'sundayPrice',
                        #  'priceTemplate_id',
                        #  'minimumDays',
                        #  'maximumDays',
                        #  'factor',
                        #  'accomodation__startDate',
                        #  'accomodation__finishDate',
                        #  'priceTemplate_id'
                    ).order_by('minimumDays')
                    for mslp in msLastPricesWithoutChildConditions:
                        print(mslp)

                    msListPriceDetails = []
                    msdayidx = 0
                    msAlldateslist = [
                        d for d in dates_bwn_twodates(date1, date2)]
                    print(msAlldateslist)
                    # alldateslist = [weekday2name(d.weekday()) for d in dates_bwn_twodates(date1, date2)]
                    print(date1)
                    print(date2)
                    for visitDay in alldateslist:
                        # listPrice += priceListByDays_updated.get(visitDay, 0)

                        dateler = date1 + timedelta(days=msdayidx)
                        print(str(dateler))
                        print(str(weekday2name(dateler.weekday())))
                        msdayidx += 1

                        # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                        # listPriceDetails.append({
                        #     str(date1 + timedelta(days=dayidx)): priceListByDays_updated.get(visitDay, 0)
                        # })
                        # listPriceDetails.append({
                        #     "date": str(date1 + timedelta(days=dayidx)),
                        #     "price": priceListByDays.get(visitDay, 0)
                        # })
                    # print('msFirstPricesWithoutChildConditions')
                    # print(msFirstPricesWithoutChildConditions)
                    # print('msLastPricesWithoutChildConditions')
                    # print(msLastPricesWithoutChildConditions)

            # original single accomodation span search
            # accomodationsInDates = list(Accomodation.objects.filter(
            #     otel_id=i,
            #     startDate__lte=startDate,
            #     finishDate__gte=finishDate,
            #     isActive=True).values_list('id', flat=True))

            accomodationsInDates = list(Accomodation.objects.filter(otel_id=i).filter(
                # (Q(startDate__range=[startDate, finishDate]) &
                # Q(finishDate__range=[startDate, finishDate])),
                (Q(startDate__lte=startDate) & Q(finishDate__gte=startDate)),
                (Q(startDate__lte=finishDate) & Q(finishDate__gte=finishDate)),
                # startDate__lte=startDate,
                # finishDate__gte=finishDate,
                isActive=True).values_list('id', flat=True))

            print('accomodationsInDates')
            print(accomodationsInDates)

            priceItem['accomodationsInDates'] = accomodationsInDates
            priceItem['priceItems'] = []
            # .filter(reduce(operator.or_, (Q(priceTemplate__roomType__feature__name__icontains=x) for x in keywords))
            #     priceTemplate__roomType__feature__name__icontains=keywords)

            for acs in accomodationsInDates:
                fiyatsForAcsList = []
                pricesWithoutChildConditions = PriceDetails.objects.filter(
                    otel_id=i,
                    accomodation_id=acs,
                    adultCount__exact=adultCount,
                    childCount__exact=childCount,
                    isActive=True).values('id').order_by('minimumDays')
                pricesWithoutChildConditionsList = []
                print(
                    'pricesWithoutChildConditions----------------------------------------')
                print(pricesWithoutChildConditions)
                print(
                    'EOF pricesWithoutChildConditions----------------------------------------')

                for pw in pricesWithoutChildConditions:
                    print(pw['id'])
                    # print('childConds')
                    # print(childConditions)
                    pd = PriceDetails.objects.get(pk=pw['id'])
                    if childCount == 0:
                        pdekle = PriceDetails.objects.values('id',
                                                             'otel_id',
                                                             'adultCount', 'childCount', 'factor',
                                                             'currency_id',
                                                             'currency__name',
                                                             'mondayManuelPrice', 'mondayPerPersonPrice',
                                                             'mondayPrice',
                                                             'tuesdayManuelPrice', 'tuesdayPerPersonPrice',
                                                             'tuesdayPrice',
                                                             'wednesdayManuelPrice',
                                                             'wednesdayPerPersonPrice',
                                                             'wednesdayPrice',
                                                             'thursdayManuelPrice',
                                                             'thursdayPerPersonPrice',
                                                             'thursdayPrice',
                                                             'fridayManuelPrice', 'fridayPerPersonPrice',
                                                             'fridayPrice',
                                                             'saturdayManuelPrice',
                                                             'saturdayPerPersonPrice',
                                                             'saturdayPrice',
                                                             'sundayManuelPrice', 'sundayPerPersonPrice',
                                                             'sundayPrice',
                                                             'priceTemplate_id',
                                                             'minimumDays',
                                                             'maximumDays',
                                                             'factor',
                                                             # 'accomodation_id__isBundleDays').get(pk=pw['id'])
                                                             'accomodation_id__isBundleDays').get(pk=pd.id)
                        # print(pdekle)
                        fiyatsForAcsList.append(pdekle)

                    childCondsForLoop = list(
                        pd.childCondition.values('startAge', 'finishAge').all())

                    hitCounter = 0
                    for cc in childConditions:
                        for ccfl in childCondsForLoop:
                            if ccfl['startAge'] <= cc <= ccfl['finishAge']:
                                print('hit')
                                hitCounter += 1
                                print('hitCounter {}'.format(hitCounter))
                                print('childCount {}'.format(childCount))

                                if hitCounter == childCount:
                                    print(" hit bulundu {} ".format(pd.id))
                                    pdekle = PriceDetails.objects.values('id',
                                                                         'otel_id',
                                                                         'adultCount', 'childCount', 'factor',
                                                                         'currency_id',
                                                                         'currency__name',
                                                                         'mondayManuelPrice', 'mondayPerPersonPrice',
                                                                         'mondayPrice',
                                                                         'tuesdayManuelPrice', 'tuesdayPerPersonPrice',
                                                                         'tuesdayPrice',
                                                                         'wednesdayManuelPrice',
                                                                         'wednesdayPerPersonPrice',
                                                                         'wednesdayPrice',
                                                                         'thursdayManuelPrice',
                                                                         'thursdayPerPersonPrice',
                                                                         'thursdayPrice',
                                                                         'fridayManuelPrice', 'fridayPerPersonPrice',
                                                                         'fridayPrice',
                                                                         'saturdayManuelPrice',
                                                                         'saturdayPerPersonPrice',
                                                                         'saturdayPrice',
                                                                         'sundayManuelPrice', 'sundayPerPersonPrice',
                                                                         'sundayPrice',
                                                                         'priceTemplate_id',
                                                                         'minimumDays',
                                                                         'maximumDays',
                                                                         'factor',
                                                                         'accomodation_id__isBundleDays').get(pk=pd.id)
                                    # print(pdekle)
                                    fiyatsForAcsList.append(pdekle)
                                    # hitCounter=0

                fiyatsForAcs = fiyatsForAcsList
                f = {}
                if fiyatsForAcs:
                    priceListByDays = {}
                    f['accomodation'] = acs
                    import time
                    markup = MarkUp.objects.filter(otel=i).filter(
                        (Q(startDate__lte=startDate) | Q(
                            startTime__lte=time.strftime('%X'))),
                        (Q(finishDate__gte=finishDate) | Q(
                            finishTime__gte=time.strftime('%X'))),
                        isActive=True).first()

                    # if markup:
                    #     print('---------markup-------')
                    #     print(markup.id)
                    #     print(markup.discountAmount)
                    #     print(markup.discountType)
                    #     f['markupAmount'] = markup.discountAmount
                    #     if markup.discountType ==1:
                    #         f['markupType'] = "Tutar"
                    #     if markup.discountType ==2:
                    #         f['markupType'] = "Yuzde"

                    mindays = []
                    pricedetails = []
                    numofelement = []

                    for facs in fiyatsForAcs:
                        # print(facs['id'])
                        # print(facs)
                        f['priceID'] = facs['id']
                        # print(facs['id'])
                        # pricebyid = list(PriceDetails.objects.get(pk=facs['id']).childCondition.values_list('id', flat=True).all())
                        # print(pricebyid)
                        # print(pricebyid.childCondition.values_list('id', flat=True).all())
                        pt = PriceTemplate.objects.get(
                            pk=facs['priceTemplate_id'])

                        minDays = facs['minimumDays']
                        ptDays = daysT2E(
                            list(pt.days.values_list('name', flat=True).all()))
                        numOfElements = numOfElementsInList(
                            ptDays, alldateslist)
                        mindays.append(minDays)
                        numofelement.append(numOfElements)
                        if numOfElements >= minDays:
                            # if numOfElementsInList(ptDays, alldateslist) == minDays:
                            pricedetails.append(pt.id)
                            ptDaysId = list(pt.days.values_list(
                                'id', flat=True).all())
                            for d in ptDaysId:
                                dayName = weekday2name(d - 1)
                                dayPrice = facs[dayName + 'Price']
                                priceListByDays[dayName] = dayPrice

                    # print("priceListByDays {}".format(priceListByDays))
                    listPriceDetails = []
                    listPrice = 0
                    dayidx = 0

                    for visitDay in alldateslist:
                        listPrice += priceListByDays.get(visitDay, 0)
                        dayidx += 1
                        listPriceDetails.append({
                            "date": str(date1 + timedelta(days=dayidx)),
                            "price": priceListByDays.get(visitDay, 0)
                        })

                    acc = Accomodation.objects.get(pk=acs)
                    ptds = PriceTemplateDetail.objects.filter(
                        adultCount=adultCount, roomType=acc.roomType.id)
                    childConds = []
                    if ptds:
                        for p in ptds:
                            childConds.append({
                                "adultCount": p.adultCount,
                                "childCount": p.childCount,
                                "factor": p.factor,
                                "conditions": p.childCondition_text
                            })
                    # (1, 'Net Fiyat'),
                    # (2, 'Komisyonlu Fiyat'),
                    kontenjan = Quota.objects.filter(otel=i,
                                                     quotaDate__gte=startDate,
                                                     quotaDate__lte=finishDate,
                                                     roomType=acc.roomType.id,
                                                     isActive=True
                                                     ).values_list('quotaDate', flat=True).all()
                    # print('unavailavble days')
                    # print(kontenjan)
                    if kontenjan:
                        f['isPriceAvailable'] = False
                        f['unavailableDays'] = list(kontenjan)
                    else:
                        f['isPriceAvailable'] = True
                        f['unavailableDays'] = []
                    f['childConditions'] = childConds
                    f['priceListByDays'] = priceListByDays
                    # f['numofelement'] = numofelement
                    # f['mindays'] = mindays
                    # f['pricedetails'] = pricedetails
                    # print(acc.currency.name)
                    f['accomodation__roomType'] = acc.roomType.id
                    f['accomodation__roomType__name'] = acc.roomType.name
                    f['accomodation__roomType__name1'] = acc.roomType.name
                    # f['accomodation__roomType__description'] = acc.roomType.description
                    f['accomodation__roomType__roomSize'] = acc.roomType.roomSize
                    f['accomodation__roomType__guestCount'] = acc.roomType.guestCount
                    # odaResimleri = OtelImages.objects.filter(roomType=acc.roomType.id)
                    # print('odaResimleri')
                    # print(odaResimleri)

                    odaResimleriDefault = []
                    try:
                        odaImagesDefault = OtelImages.objects.filter(
                            roomType=acc.roomType.id, isDefault=True)
                        # odaImages = OtelImages.objects.filter(roomType=112)
                    except OtelImages.DoesNotExist:
                        odaImagesDefault = None

                    if odaImagesDefault:
                        odaResimleriDefault = list(
                            odaImagesDefault.values('title', 'file').all())

                    f['accomodation__roomType__images_default'] = odaResimleriDefault

                    odaResimleri = []
                    try:
                        odaImages = OtelImages.objects.filter(
                            roomType=acc.roomType.id, isDefault=False)
                        # odaImages = OtelImages.objects.filter(roomType=112)
                    except OtelImages.DoesNotExist:
                        odaImages = None

                    if odaImages:
                        odaResimleri = list(
                            odaImages.values('title', 'file').all())

                    f['accomodation__roomType__images'] = odaResimleri

                    f['accomodation__pensionType'] = acc.concept.id
                    f['accomodation__pensionType__name'] = acc.concept.name
                    f['currency_id'] = acc.currency.id
                    f['currency_name'] = acc.currency.name
                    f['priceFactor'] = facs['factor']
                    f['roomFeatures'] = list(
                        acc.roomType.feature.values_list('name', flat=True).all())
                    # print(acc.roomType.name)
                    # print(type(acc.roomType.roomSize))
                    calcType = acc.priceCalcType
                    # print(acc.priceCalcType)
                    kickbackInDates = KickBack.objects.filter(otel_id=i, startDate__lte=startDate,
                                                              finishDate__gte=finishDate,
                                                              isActive=True).values('id',
                                                                                    'amount',
                                                                                    'isKademeliKumulatif').first()
                    print('kickbackInDates')
                    print(kickbackInDates)
                    if kickbackInDates:
                        # print(kickbackInDates['amount'])
                        # print(kickbackInDates['isKademeliKumulatif'])
                        kickbackAmount = kickbackInDates['amount']
                        isKickbackKademeli = kickbackInDates['isKademeliKumulatif']
                    else:
                        kickbackAmount = 0
                        isKickbackKademeli = False
                    # genel aksiyon var mi?
                    actionsInDates = ActionsDetail.objects.filter(
                        (Q(isApplyAllRoomTypes=True) | Q(
                            roomType__in=[f['accomodation__roomType']])),
                        # (Q(actions__id=2) & ~Q(totalDays__lte=len(alldateslist))),
                        (Q(actions__id=1)),
                        otel_id=i,
                        startDate__lte=startDate,
                        finishDate__gte=finishDate,

                        isActive=True).values(
                        # (isApplyAllRoomTypes=True) or (roomType=f['accomodation__roomType'])).values(
                        'id', 'hotelCommission', 'saleDiscount', 'isKademeli', 'fakeRate',
                        'discountRate', 'actions__name', 'actions_id',
                        'isApplyAllRoomTypes', 'roomType',
                        'dayActionCalculation', 'totalDays', 'paidDays', 'minKonaklama', 'webDescription').all().distinct('id',
                                                                                                                          'actions_id').order_by(
                        'actions_id')
                    # once sartlari uymayan gun aksiyonlarini cikartalim
                    # actionsInDates = actionsInDates.exclude(
                    #     (Q(actions__id=2) & ~Q(minKonaklama__lte=len(alldateslist))))
                    # actionsInDates = actionsInDates.exclude(Q(actions=2))
                    # print('actionsInDates')
                    # print(actionsInDates)

                    f['listPrice'] = listPrice
                    f['cancelInsuranceAmount'] = 11
                    e = ExtraServices.objects.filter(serviceType=1, otel__in=[i]).filter(
                        Q(lowerLimit__lte=listPrice) & Q(upperLimit__gte=listPrice)).first().values('price')
                    print('d22-----------------------------------')
                    print(e['price'])
                    priceListByDays_updated = {}

                    maliyet = listPrice
                    actionsApplied = []
                    if actionsInDates:
                        actionInDate = actionsInDates.first()
                        otherActions = ActionsDetail.objects.get(pk=actionInDate['id']).otherAction.filter(
                            startDate__lte=startDate,
                            finishDate__gte=finishDate,
                            isActive=True).values(
                            'id',
                            'hotelCommission',
                            'saleDiscount',
                            'isKademeli',
                            'fakeRate',
                            'discountRate',
                            'actions__name',
                            'actions_id',
                            'isApplyAllRoomTypes',
                            'roomType',
                            'dayActionCalculation',
                            'totalDays',
                            'paidDays',
                            'minKonaklama',
                            'webDescription').all().distinct('id', 'actions_id')
                        # print(otherActions)
                        otherActions = otherActions.exclude(
                            (Q(actions__id=2) & ~Q(minKonaklama__lte=len(alldateslist))))
                        # print(otherActions.count())
                        # print(otherActions)

                        # otherActions = actionInDate.otherAction.objects.all()
                        # print(actionInDate)
                        hotelCommision = actionInDate['hotelCommission']
                        saleDiscount = actionInDate['saleDiscount']
                        discountRate = actionInDate['discountRate']
                        isAksiyonKademeli = actionInDate['isKademeli']
                        kickbackDiscountAmount = 0
                        if not otherActions:
                            # Eger bagli alt aksiyon yoksa
                            maliyet_old = maliyet
                            maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                maliyet, calcType,
                                isAksiyonKademeli,
                                hotelCommision, discountRate,
                                isKickbackKademeli,
                                kickbackAmount, saleDiscount)
                            for key, value in priceListByDays.items():
                                value_updated, _, _, _, _ = calculateCost(
                                    value, calcType,
                                    isAksiyonKademeli,
                                    hotelCommision, discountRate,
                                    isKickbackKademeli,
                                    0, saleDiscount)
                                priceListByDays_updated[key] = value_updated
                            priceListByDays_updated = dict(sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                                                  reverse=False))
                            print(" maliyet, afiseFiyat, satisFiyati, karlilik")
                            print(" {:2f}       {:2f}          {:2f}           {:2f} ".format(maliyet, afiseFiyat,
                                                                                              satisFiyati, karlilik))
                            # if markup:
                            #     1 tutar 2 yuzde
                            #     if markup.discountType == 2:
                            #         satisFiyati = satisFiyati * (100 - markup.discountAmount)/100
                            #     if markup.discountType == 1:
                            #         satisFiyati = satisFiyati - markup.discountAmount

                            f['maliyet'] = maliyet
                            f['afiseFiyat'] = afiseFiyat
                            f['satisFiyati'] = satisFiyati
                            f['karlilik'] = karlilik
                            f['kickbackTutari'] = kbTutari
                            # maliyet, afiseFiyat, satisFiyati, karlilik)

                            # print(" {} {} {} {} ".format(maliyet, afiseFiyat, satisFiyati,
                            #                              karlilik))
                            actionsApplied.append({
                                "action_id": actionInDate['id'],
                                "action_name": actionInDate['actions__name'],
                                "actionWebDescription": actionInDate['webDescription'],
                                "listPrice": listPrice,
                                "maliyet": maliyet,
                                "afiseFiyat": afiseFiyat,
                                "satisFiyati": satisFiyati,
                                "karlilik": karlilik,
                                "aksiyonIndirimTutari": maliyet_old - maliyet,
                                "aksiyonluFiyatListesi": priceListByDays_updated
                            })
                            listPriceDetails = []
                            dayidx = 0
                            for visitDay in alldateslist:
                                # listPrice += priceListByDays_updated.get(visitDay, 0)
                                dayidx += 1

                                # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                                # listPriceDetails.append({
                                #     str(date1 + timedelta(days=dayidx)): priceListByDays_updated.get(visitDay, 0)
                                # })
                                listPriceDetails.append({
                                    "date": str(date1 + timedelta(days=dayidx)),
                                    "price": priceListByDays.get(visitDay, 0)
                                })

                            print(listPriceDetails)

                        else:
                            print('# Eger bagli alt aksiyon(lar) VARSA')
                            for oa in otherActions:
                                print(oa)
                            maliyet_old = maliyet
                            maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                maliyet, calcType,
                                isAksiyonKademeli,
                                hotelCommision, discountRate,
                                isKickbackKademeli,
                                0, saleDiscount)
                            for key, value in priceListByDays.items():
                                value_updated, _, _, _, _ = calculateCost(
                                    value, calcType,
                                    isAksiyonKademeli,
                                    hotelCommision, discountRate,
                                    isKickbackKademeli,
                                    0, saleDiscount)
                                priceListByDays_updated[key] = value_updated
                                # priceListByDays_updated.append(key+'_': value_updated)
                            priceListByDays_updated = dict(
                                sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                       reverse=False))
                            # print(priceListByDays_updated)
                            print(" maliyet, afiseFiyat, satisFiyati, karlilik")
                            print(" {:2f}       {:2f}          {:2f}           {:2f} ".format(maliyet, afiseFiyat,
                                                                                              satisFiyati, karlilik))
                            listPriceDetails = []
                            dayidx = 0
                            for visitDay in alldateslist:
                                # listPrice += priceListByDays_updated.get(visitDay, 0)
                                dayidx += 1
                                # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                                # listPriceDetails.append({
                                #     str(date1 + timedelta(days=dayidx)):
                                #     priceListByDays_updated.get(visitDay, 0)
                                # })
                                listPriceDetails.append({
                                    "date": str(date1 + timedelta(days=dayidx)),
                                    "price": priceListByDays.get(visitDay, 0)
                                })

                            print(listPriceDetails)
                            if markup:
                                # 1 tutar 2 yuzde
                                if markup.discountType == 2:
                                    satisFiyati = satisFiyati * \
                                        (100 - markup.discountAmount)/100
                                if markup.discountType == 1:
                                    satisFiyati = satisFiyati - markup.discountAmount

                            f['maliyet'] = maliyet
                            f['afiseFiyat'] = afiseFiyat
                            f['satisFiyati'] = satisFiyati
                            f['karlilik'] = karlilik
                            f['kickbackTutari'] = kbTutari

                            # maliyet, afiseFiyat, satisFiyati, karlilik)

                            # print(" {} {} {} {} ".format(maliyet, afiseFiyat, satisFiyati,
                            #                              karlilik))
                            actionsApplied.append({
                                "action_id": actionInDate['id'],
                                "action_name": actionInDate['actions__name'],
                                "actionWebDescription": actionInDate['webDescription'],
                                "listPrice": listPrice,
                                "maliyet": maliyet,
                                "afiseFiyat": afiseFiyat,
                                "satisFiyati": satisFiyati,
                                "karlilik": karlilik,
                                "aksiyonIndirimTutari": maliyet_old - maliyet,
                                "aksiyonluFiyatListesi": priceListByDays_updated
                            })
                            actionslist_len = len(otherActions)
                            for index, acid in enumerate(otherActions):
                                print('actions_id')
                                print(acid['actions_id'])
                                if acid['actions_id'] == 2:
                                    # gun aksyionu
                                    unpaidDays = acid['minKonaklama'] - \
                                        acid['paidDays']
                                    discountAmount = unpaidDays * \
                                        (list(
                                            priceListByDays_updated.values())[0])
                                    print("Gun aksyionu uygulaniyor [Indirim tutari= {}]".format(
                                        discountAmount))
                                    maliyet_old = maliyet
                                    maliyet -= discountAmount
                                    afiseFiyat -= discountAmount
                                    satisFiyati -= discountAmount

                                    if index == actionslist_len - 1:
                                        maliyet_old = maliyet
                                        maliyet = maliyet * \
                                            (1 - kickbackAmount / 100)
                                        afiseFiyat = afiseFiyat * \
                                            (1 - kickbackAmount / 100)
                                        satisFiyati = satisFiyati * \
                                            (1 - kickbackAmount / 100)
                                        print(' KICKback uygulandi {:2f}'.format(
                                            kickbackAmount))

                                    karlilik = (
                                        satisFiyati - maliyet) / satisFiyati
                                    # karlilik = (satisFiyati - maliyet) /

                                    maliyet = round(maliyet, 2)
                                    afiseFiyat = round(afiseFiyat, 2)
                                    satisFiyati = round(satisFiyati, 2)
                                    karlilik = round(karlilik * 100, 2)
                                    # f['kickbackAmount'] = maliyet_old - maliyet

                                    listPriceDetails = []
                                    dayidx = 0
                                    for visitDay in alldateslist:
                                        # listPrice += priceListByDays_updated.get(visitDay, 0)
                                        dayidx += 1
                                        if dayidx <= len(alldateslist) - unpaidDays:
                                            # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(visitDay, 0)
                                            #
                                            # listPriceDetails.append({
                                            #     str(date1 + timedelta(days=dayidx)): priceListByDays_updated.get(visitDay, 0)
                                            # })
                                            listPriceDetails.append({
                                                "date": str(date1 + timedelta(days=dayidx)),
                                                "price": priceListByDays.get(visitDay, 0)
                                            })
                                        else:
                                            # listPriceDetails[str(date1 + timedelta(days=dayidx))] = 0
                                            # listPriceDetails.append({
                                            #     str(date1 + timedelta(days=dayidx)): 0})

                                            listPriceDetails.append({
                                                "date": str(date1 + timedelta(days=dayidx)),
                                                "price": 0
                                            })

                                    print(listPriceDetails)

                                if acid['actions_id'] in [3, 4, 5, 6]:
                                    print('Genel aksiyon uygulandi..')
                                    hotelCommision = acid['hotelCommission']
                                    saleDiscount = acid['saleDiscount']
                                    discountRate = acid['discountRate']
                                    isAksiyonKademeli = acid['isKademeli']

                                    if index == actionslist_len - 1:
                                        maliyet_old = maliyet
                                        maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                            maliyet, calcType,
                                            isAksiyonKademeli,
                                            hotelCommision, discountRate,
                                            isKickbackKademeli,
                                            kickbackAmount, saleDiscount)
                                        f['kickbackAmount'] = maliyet_old - maliyet
                                        for key, value in priceListByDays.items():
                                            value_updated, _, _, _, _ = calculateCost(
                                                value, calcType,
                                                isAksiyonKademeli,
                                                hotelCommision, discountRate,
                                                isKickbackKademeli,
                                                0, saleDiscount)
                                            priceListByDays_updated[key] = value_updated
                                        priceListByDays_updated = dict(
                                            sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                                   reverse=False))
                                        listPriceDetails = []
                                        dayidx = 0
                                        for visitDay in alldateslist:
                                            # listPrice += priceListByDays_updated.get(visitDay, 0)
                                            dayidx += 1
                                            # listPriceDetails[str(date1 + timedelta(days=dayidx))] = priceListByDays_updated.get(
                                            #     visitDay, 0)
                                            # listPriceDetails.append({
                                            #     str(date1 + timedelta(days=dayidx)): priceListByDays_updated.get(
                                            #         visitDay, 0)
                                            # })
                                            listPriceDetails.append({
                                                "date": str(date1 + timedelta(days=dayidx)),
                                                "price": priceListByDays.get(visitDay, 0)
                                            })

                                        print(listPriceDetails)
                                    else:
                                        maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                            maliyet, calcType,
                                            isAksiyonKademeli,
                                            hotelCommision, discountRate,
                                            isKickbackKademeli,
                                            0, saleDiscount)
                                        for key, value in priceListByDays.items():
                                            value_updated, _, _, _, kbTutari = calculateCost(
                                                value, calcType,
                                                isAksiyonKademeli,
                                                hotelCommision, discountRate,
                                                isKickbackKademeli,
                                                0, saleDiscount)
                                            priceListByDays_updated[key] = value_updated
                                            # priceListByDays_updated.append(key+'_': value_updated)
                                        priceListByDays_updated = dict(
                                            sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                                   reverse=False))
                                if markup:
                                    # 1 tutar 2 yuzde
                                    if markup.discountType == 2:
                                        satisFiyati = satisFiyati * \
                                            (100 - markup.discountAmount) / 100
                                    if markup.discountType == 1:
                                        satisFiyati = satisFiyati - markup.discountAmount
                                actionsApplied.append({
                                    "action_id": acid['id'],
                                    "action_name": acid['actions__name'],
                                    "actionWebDescription": acid['webDescription'],
                                    "listPrice": listPrice,
                                    "maliyet": maliyet,
                                    "afiseFiyat": afiseFiyat,
                                    "satisFiyati": satisFiyati,
                                    "karlilik": karlilik,
                                    "aksiyonIndirimTutari": maliyet_old - maliyet,
                                    "aksiyonluFiyatListesi": priceListByDays_updated
                                })
                    else:
                        print('no actions get contract')
                        c = Contract.objects.filter(otel_id=i, startDate__lte=startDate,
                                                    finishDate__gte=finishDate,
                                                    isActive=True).values('id',
                                                                          'commissionRate').order_by('id').last()
                        print(c)
                        f['acc_id'] = 0
                        f['maliyet'] = 0
                        f['afiseFiyat'] = 0
                        f['satisFiyati'] = 0
                        f['karlilik'] = 0
                    f['listPriceDetails'] = listPriceDetails
                    f['actionsApplied'] = actionsApplied
                if f:
                    priceItem['priceItems'].append(f)
                    resultCount += 1
            if len(priceItem['priceItems']) > 0:
                response["prices"].append(priceItem)
        response['otelsFound'] = len(response["prices"])
        response['pricesFound'] = resultCount

        try:
            # searchQuery =
            searchKeyword = request.data['keyword']
            searchStartDate = request.data['startDate']
            searchFinishDate = request.data['finishDate']
            if ('otelId' in request.data.keys()):
                searchOtelId = request.data['otelId']
            else:
                searchOtelId = None
            searchChildCondition = request.data['childConditions']
            searchAdultCount = int(request.data['adultCount'])
            searchChildCount = int(request.data['childCount'])
            searchFoundOtelIds = response['otelsFound']
            searchFoundPrices = response["prices"]
            searchResultCount = resultCount
        # TODO loglama burada
        except:
            pass
        return Response(response)


class AnonimSearchApiView(LoggingMixin, CreateAPIView):
    # this api will be anonimous and implemnent GET/Retrieve only
    authentication_classes = []
    permission_classes = []
    serializer_class = serializers.Serializer
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):

        def weekday2name(weekday):
            days = ["monday", "tuesday", "wednesday",
                    "thursday", "friday", "saturday", "sunday"]
            return days[weekday]

        def dates_bwn_twodates(start_date, end_date):
            for n in range(int((end_date - start_date).days)):
                yield start_date + timedelta(n)

        def recursively_prune_dict_keys(obj, keep):
            if isinstance(obj, dict):
                return {k: recursively_prune_dict_keys(v, keep) for k, v in obj.items() if k in keep}
            elif isinstance(obj, list):
                return [recursively_prune_dict_keys(item, keep) for item in obj]
            else:
                return obj

        def sublist(lst1, lst2):
            if not lst1:
                return False
            ls1 = [element for element in lst1 if element in lst2]
            return ls1 == lst1

        def getbundledays(fromday, plus):
            retDays = []
            for d in range(fromday - 1, fromday + plus - 1):
                # print(weekday2name(d))
                retDays += [weekday2name(d)]
            return retDays

        def numOfElementsInList(listA, listB):
            """ determine number of elements of lista in listb            """
            t = 0
            for le in listA:
                if le in listB:
                    t += 1
            return t

        def daysT2E(daylist):
            daysTR = ['Pazartesi', 'Salı', 'Çarşamba',
                      'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            daysEN = ["monday", "tuesday", "wednesday",
                      "thursday", "friday", "saturday", "sunday"]
            r = []
            for d in daylist:
                r.append(daysEN[daysTR.index(d)])
            return r

        def calculateCost(fiyat, calcType, isAksiyonKademeli, hotelCommision, saleDiscount, isKickbackKademeli,
                          kickback, afiseOrani=0):
            """
            reutnr maliyet, afiseFiyati, satis fiyati, karlilik
            """
            if saleDiscount:
                saleDiscount = saleDiscount / 100
            else:
                saleDiscount = 0

            if hotelCommision:
                hotelCommision = hotelCommision / 100
            else:
                hotelCommision = 0
            if kickback:
                kickback = kickback / 100
            else:
                kickback = 0
            if afiseOrani:
                afiseOrani = afiseOrani / 100
            else:
                afiseOrani = 0
            # calcType options
            # (1, 'Net Fiyat'),
            # (2, 'Komisyonlu Fiyat'),
            maliyet = 0
            if calcType == 2:
                if isKickbackKademeli:
                    # kickback kademeli
                    if isAksiyonKademeli:
                        # aksiyon kadememi
                        maliyet = (1 - hotelCommision) * \
                            (1 - saleDiscount) * (1 - kickback) * fiyat
                        maliyet_kbsiz = (1 - hotelCommision) * \
                            (1 - saleDiscount) * fiyat

                    else:
                        # aksiyon kumulatif
                        maliyet = (1 - (hotelCommision + saleDiscount)
                                   ) * (1 - kickback) * fiyat
                        maliyet_kbsiz = (
                            1 - (hotelCommision + saleDiscount)) * fiyat
                else:
                    # kickback = kumulatif
                    if isAksiyonKademeli:
                        # aksiyon kadememi
                        maliyet = (((1 - hotelCommision) *
                                   (1 - saleDiscount)) - kickback) * fiyat
                        maliyet_kbsiz = (
                            ((1 - hotelCommision) * (1 - saleDiscount))) * fiyat

                    else:
                        # aksiyon kumulatif
                        maliyet = (
                            (1 - (hotelCommision + saleDiscount)) - kickback) * fiyat
                        maliyet_kbsiz = (
                            (1 - (hotelCommision + saleDiscount))) * fiyat

                afiseFiyat = fiyat
                satisFiyati = afiseFiyat * (1 - afiseOrani)
                if satisFiyati == 0:
                    satisFiyati = 1
                karlilik = (satisFiyati - maliyet) / satisFiyati
                kbTutari = maliyet_kbsiz - maliyet

            if calcType == 1:
                kbTutari = 0
                if isAksiyonKademeli:
                    # aksiyon kademeli
                    maliyet = fiyat * (1 - hotelCommision)
                    toplamKomisyon = (1 - (1 - hotelCommision)
                                      * (1 - saleDiscount))
                    afiseFiyat = maliyet / (1 - toplamKomisyon)
                    satisFiyati = afiseFiyat * (1 - afiseOrani)
                    karlilik = (satisFiyati - maliyet) / satisFiyati

                else:
                    # Aksiyn kumulatif
                    maliyet = fiyat * (1 - hotelCommision)
                    toplamKomisyon = hotelCommision + saleDiscount
                    afiseFiyat = maliyet / (1 - toplamKomisyon)
                    satisFiyati = afiseFiyat * (1 - afiseOrani)
                    karlilik = (satisFiyati - maliyet) / satisFiyati

            return round(maliyet, 2), round(afiseFiyat, 2), round(satisFiyati, 2), round(karlilik * 100, 2), round(
                kbTutari, 2)

        keyword = request.data['keyword']
        startDate = request.data['startDate']
        finishDate = request.data['finishDate']

        if ('otelId' in request.data.keys()):
            otelId = request.data['otelId']

        else:
            otelId = None

        if not otelId:
            print("no otel no problem")
        else:
            print("yes otel full problem")
            print(otelId)

        if ('adultCount' in request.data.keys()):
            adultCount = int(request.data['adultCount'])
        else:
            adultCount = 0

        if ('childCount' in request.data.keys()):
            childCount = int(request.data['childCount'])
        else:
            childCount = 0
        # print(childCount)
        # print(request.data.keys())
        if ('advancedSearch' in request.data.keys()) and request.data['advancedSearch'] is True:
            advancedSearch = True
            advancedPriceList = []
        else:
            advancedSearch = False

        if 'childConditions' in request.data.keys():
            childConditions = request.data['childConditions']
        else:
            childConditions = []

        if 'countryID' in request.data.keys():
            countryID = request.data['countryID']
        else:
            countryID = None
        #
        # print('chidlConditions')
        # print(chidlConditions)

        import datetime
        date1 = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(finishDate, "%Y-%m-%d").date()
        alldateslist = [weekday2name(d.weekday())
                        for d in dates_bwn_twodates(date1, date2)]
        if keyword != "":
            keywords = keyword.split()
        else:
            keywords = [""]
        print(keywords)
        response = {'keyword': keyword}

        if not otelId:
            byotelvalues_distinct = list(
                Otel.objects.filter(isActive=True, isStatusActive=True).filter(
                    reduce(operator.or_, ((Q(region_text__icontains=x) | Q(location_text__icontains=x) | Q(
                        region_text__icontains=x) | Q(name__icontains=x)) for x in
                        keywords))).values_list('id', flat=True).distinct())
            byfeatures_distinct = list(
                OtelFeatures.objects.filter(otel__isActive=True, otel__isStatusActive=True).filter(
                    reduce(operator.or_, (Q(feature_text__icontains=x) for x in keywords))).values_list(
                    'otel', flat=True).distinct())
            # byroomfeatures = list(PriceDetails.objects.filter(
            #     reduce(operator.or_, (Q(priceTemplate__roomType__feature__name__icontains=x) for x in keywords))
            # ).values_list('otel', flat=True).distinct())
            # print('byroomfeatures')
            # print(byroomfeatures)
            # otelslist = byfeatures_distinct + byotelvalues_distinct+byroomfeatures
            otelslist = byfeatures_distinct + byotelvalues_distinct

        else:
            otelslist = [otelId]

        otelslist = list(set(otelslist))
        response["otels"] = otelslist
        response['daysOfStay'] = alldateslist
        response["prices"] = []
        resultCount = 0
        fiyatListesi = []
        if not otelslist:
            response['otelsFound'] = 0
            response['pricesFound'] = 0
            return Response(response)
        for i in otelslist:
            priceItem = {}
            otelimages = []
            # resultCount = 0
            # geolocation ekleme

            from django.contrib.gis.geoip2 import GeoIP2
            from geoip2.errors import AddressNotFoundError
            g = GeoIP2()
            try:
                client_ip = request.META['HTTP_X_REAL_IP']
            except:
                client_ip = '127.0.0.1'
            location = {}
            try:
                location = g.city(client_ip)
            except AddressNotFoundError:
                location = "No location"
                # location["country_code"] = "TR"
            priceItem['location'] = location

            # geolocation ekleme

            # if currencyID == None:
            #     doviz = "USD"
            #     dovizID = 2
            #     if location != "No location":
            #         if location["country_name"] == "Turkey":
            #             doviz = "TR"
            #             dovizID = 1
            #         if location["is_in_european_union"] == True:
            #             doviz = "EUR"
            #             dovizID = 3
            # else:
            #     dovizID = currencyID
            #     if dovizID == 1:
            #         doviz = "TR"
            #     if dovizID == 2:
            #         doviz = "USD"
            #     if dovizID == 3:
            #         doviz = "EUR"

            if countryID == None:

                if location == "No location":
                    # default location
                    # country = CountryGrouping.objects.filter(code2="TR").first()
                    country_code = "TR"
                    country_ID = 237
                    country_currency_id = 1
                    country_currency_name = "TL"
                else:
                    # currencyCountryGroup =CurrencyCountryGroup.objects.filter(country__in)
                    country = CountryGrouping.objects.filter(
                        code2=location["country_code"]).first()
                    cg1 = CurrencyCountryGroup.objects.filter(
                        country__in=[country.id]).first()
                    # country.countryGroup.
                    #     = CountryGrouping.objects.filter(code2=location["country_code"]).first()
                    if cg1 != None:
                        country_code = location["country_code"]
                        country_ID = country.id
                        country_currency_id = cg1.currency.id
                        country_currency_name = cg1.currency.name
                    else:
                        country_code = "TR"
                        country_ID = 237
                        country_currency_id = 1
                        country_currency_name = "TL"

            else:
                country = CountryGrouping.objects.get(pk=countryID)
                country_code = country.code2
                country_ID = country.id
                country_currency_id = country.currencyCountryGroup.currency.id
                country_currency_name = country.currencyCountryGroup.currency.name

            actual_price_details_json = {}
            actual_price_details_json['country_code'] = country_code
            actual_price_details_json['country_ID'] = country_ID
            actual_price_details_json['country_currency_id'] = country_currency_id
            actual_price_details_json['country_currency_name'] = country_currency_name

            priceItem['price_currency_details'] = actual_price_details_json

            # priceItem['currency'] = doviz
            # priceItem['currencyID'] = dovizID

            otel = Otel.objects.get(pk=i)
            priceItem['otel_id'] = i
            if otel.name:
                priceItem['otel__name'] = otel.name
            if otel.region.name:
                priceItem['otel__region__name'] = otel.region.name
            if otel.subRegion.name:
                priceItem['otel__subRegion__name'] = otel.subRegion.name
            if otel.location:
                priceItem['otel__location__name'] = otel.location.name
            else:
                priceItem['otel__location__name'] = ""
            campaigns = Campaign.objects.filter(otel_id=i, salesStartDate__lte=startDate,
                                                salesFinishDate__gte=finishDate,
                                                isActive=True).first()
            # print('campaigns')
            # print(campaigns.description)
            if campaigns:
                priceItem['capaignDescriptions'] = campaigns.description
            else:
                priceItem['capaignDescriptions'] = None
            priceItem['categories'] = list(
                otel.category.values_list('name', flat=True).all())
            priceItem['categories_en'] = list(
                otel.category.values_list('name_en', flat=True).all())
            priceItem['categories_ru'] = list(
                otel.category.values_list('name_ru', flat=True).all())
            priceItem['themes'] = list(
                otel.theme.values_list('name', flat=True).all())
            priceItem['themes_en'] = list(
                otel.theme.values_list('name_en', flat=True).all())
            priceItem['themes_ru'] = list(
                otel.theme.values_list('name_ru', flat=True).all())
            priceItem['airports'] = list(
                otel.airport.values_list('name', flat=True).all())
            priceItem['distancesToPOIS'] = otel.distancesToPOIS
            priceItem['extraFeatures'] = otel.extraFeatures
            otelimages = []
            try:
                images = OtelImages.objects.filter(otel_id=i)
            except OtelImages.DoesNotExist:
                images = None
            if images:
                otelimages = list(images.values('title', 'file').all())
            priceItem['images'] = otelimages

            accomodationsInDates = list(Accomodation.objects.filter(otel_id=i, startDate__lte=startDate,
                                                                    finishDate__gte=finishDate,
                                                                    currency_id=country_currency_id,
                                                                    isActive=True).values_list('id',
                                                                                               flat=True).order_by('id'))
            priceItem['accomodationsInDates'] = accomodationsInDates
            priceItem['priceItems'] = []
            # .filter(reduce(operator.or_, (Q(priceTemplate__roomType__feature__name__icontains=x) for x in keywords))
            #     priceTemplate__roomType__feature__name__icontains=keywords)

            for acs in accomodationsInDates:
                fiyatsForAcsList = []
                pricesWithoutChildConditions = PriceDetails.objects.filter(
                    otel_id=i,
                    accomodation_id=acs,
                    adultCount__exact=adultCount,
                    childCount__exact=childCount,
                    isActive=True).values('id').order_by('minimumDays')
                pricesWithoutChildConditionsList = []
                print(
                    'pricesWithoutChildConditions----------------------------------------')
                # print(pricesWithoutChildConditions)
                print(
                    'EOF pricesWithoutChildConditions----------------------------------------')

                for pw in pricesWithoutChildConditions:
                    print(pw['id'])
                    print('childConds')
                    # print(childConditions)
                    pd = PriceDetails.objects.get(pk=pw['id'])
                    if childCount == 0:
                        pdekle = PriceDetails.objects.values('id',
                                                             'otel_id',
                                                             'adultCount', 'childCount', 'factor',
                                                             'currency_id',
                                                             'currency__name',
                                                             'mondayManuelPrice', 'mondayPerPersonPrice',
                                                             'mondayPrice',
                                                             'tuesdayManuelPrice', 'tuesdayPerPersonPrice',
                                                             'tuesdayPrice',
                                                             'wednesdayManuelPrice',
                                                             'wednesdayPerPersonPrice',
                                                             'wednesdayPrice',
                                                             'thursdayManuelPrice',
                                                             'thursdayPerPersonPrice',
                                                             'thursdayPrice',
                                                             'fridayManuelPrice', 'fridayPerPersonPrice',
                                                             'fridayPrice',
                                                             'saturdayManuelPrice',
                                                             'saturdayPerPersonPrice',
                                                             'saturdayPrice',
                                                             'sundayManuelPrice', 'sundayPerPersonPrice',
                                                             'sundayPrice',
                                                             'priceTemplate_id',
                                                             'minimumDays',
                                                             'maximumDays',
                                                             'factor',
                                                             # 'accomodation_id__isBundleDays').get(pk=pw['id'])
                                                             'accomodation_id__isBundleDays').get(pk=pd.id)
                        # print(pdekle)
                        fiyatsForAcsList.append(pdekle)

                    childCondsForLoop = list(
                        pd.childCondition.values('startAge', 'finishAge').all())

                    hitCounter = 0
                    for cc in childConditions:
                        # if childCondsForLoop:

                        for ccfl in childCondsForLoop:

                            # print(' age {}'.format(cc))
                            if ccfl['startAge'] <= cc <= ccfl['finishAge']:
                                print('hit')
                                hitCounter += 1

                                # if pd.childCondition:
                                #     print(pd.childCondition.startAge)
                                print('hitCounter {}'.format(hitCounter))
                                print('childCount {}'.format(childCount))

                                if hitCounter == childCount:
                                    print(" hit bulundu {} ".format(pd.id))
                                    pdekle = PriceDetails.objects.values('id',
                                                                         'otel_id',
                                                                         'adultCount', 'childCount', 'factor',
                                                                         'currency_id',
                                                                         'currency__name',
                                                                         'mondayManuelPrice', 'mondayPerPersonPrice',
                                                                         'mondayPrice',
                                                                         'tuesdayManuelPrice', 'tuesdayPerPersonPrice',
                                                                         'tuesdayPrice',
                                                                         'wednesdayManuelPrice',
                                                                         'wednesdayPerPersonPrice',
                                                                         'wednesdayPrice',
                                                                         'thursdayManuelPrice',
                                                                         'thursdayPerPersonPrice',
                                                                         'thursdayPrice',
                                                                         'fridayManuelPrice', 'fridayPerPersonPrice',
                                                                         'fridayPrice',
                                                                         'saturdayManuelPrice',
                                                                         'saturdayPerPersonPrice',
                                                                         'saturdayPrice',
                                                                         'sundayManuelPrice', 'sundayPerPersonPrice',
                                                                         'sundayPrice',
                                                                         'priceTemplate_id',
                                                                         'minimumDays',
                                                                         'maximumDays',
                                                                         'factor',
                                                                         # 'accomodation_id__isBundleDays').get(pk=pw['id'])
                                                                         'accomodation_id__isBundleDays').get(pk=pd.id)
                                    # print(pdekle)
                                    fiyatsForAcsList.append(pdekle)
                                    # hitCounter=0

                # print('pricesWithoutChildConditions----------------------------------------')
                # print(fiyatsForAcsList)
                # fiyatsForAcs = list(
                #     PriceDetails.objects.filter(otel_id=i, accomodation_id=acs,
                #                                 adultCount__exact=adultCount,
                #                                 childCount__exact=childCount, isActive=True,
                #                                 childCondition_text__exact=childConditions).values(
                #         'id',
                #         'otel_id',
                #         'adultCount', 'childCount', 'factor', 'currency_id',
                #         # 'accomodation__concept_id', 'accomodation__startDate', 'accomodation__finishDate',
                #         'currency__name',
                #         'mondayManuelPrice', 'mondayPerPersonPrice', 'mondayPrice',
                #         'tuesdayManuelPrice', 'tuesdayPerPersonPrice', 'tuesdayPrice',
                #         'wednesdayManuelPrice', 'wednesdayPerPersonPrice', 'wednesdayPrice',
                #         'thursdayManuelPrice', 'thursdayPerPersonPrice', 'thursdayPrice',
                #         'fridayManuelPrice', 'fridayPerPersonPrice', 'fridayPrice',
                #         'saturdayManuelPrice', 'saturdayPerPersonPrice', 'saturdayPrice',
                #         'sundayManuelPrice', 'sundayPerPersonPrice', 'sundayPrice',
                #         'priceTemplate_id',
                #         'minimumDays',
                #         'maximumDays',
                #         'factor',
                #         'accomodation_id__isBundleDays',
                #     ).order_by('minimumDays'))

                fiyatsForAcs = fiyatsForAcsList
                # print(fiyatsForAcsList)
                # print(fiyatsForAcs)
                f = {}
                if fiyatsForAcs:
                    priceListByDays = {}
                    f['accomodation'] = acs
                    f['accomodation'] = acs
                    mindays = []
                    pricedetails = []
                    numofelement = []

                    for facs in fiyatsForAcs:
                        print(facs['id'])
                        print(facs)
                        f['priceID'] = facs['id']
                        # print(facs['id'])
                        # pricebyid = list(PriceDetails.objects.get(pk=facs['id']).childCondition.values_list('id', flat=True).all())
                        # print(pricebyid)
                        # print(pricebyid.childCondition.values_list('id', flat=True).all())
                        pt = PriceTemplate.objects.get(
                            pk=facs['priceTemplate_id'])

                        minDays = facs['minimumDays']
                        ptDays = daysT2E(
                            list(pt.days.values_list('name', flat=True).all()))
                        numOfElements = numOfElementsInList(
                            ptDays, alldateslist)
                        mindays.append(minDays)
                        numofelement.append(numOfElements)
                        if numOfElements >= minDays:
                            # if numOfElementsInList(ptDays, alldateslist) == minDays:
                            pricedetails.append(pt.id)
                            ptDaysId = list(pt.days.values_list(
                                'id', flat=True).all())
                            for d in ptDaysId:
                                dayName = weekday2name(d - 1)
                                dayPrice = facs[dayName + 'Price']
                                priceListByDays[dayName] = dayPrice

                    # print("priceListByDays {}".format(priceListByDays))
                    listPrice = 0
                    for visitDay in alldateslist:
                        listPrice += priceListByDays.get(visitDay, 0)

                    # print("listPrice {}".format(listPrice))

                    acc = Accomodation.objects.get(pk=acs)
                    ptds = PriceTemplateDetail.objects.filter(adultCount=adultCount,
                                                              roomType=acc.roomType.id)
                    childConds = []
                    if ptds:
                        for p in ptds:
                            print(p)
                            # print(p.childCount)
                            # print(p.factor)
                            # print(p.childCondition_text)

                            childConds.append({
                                "adultCount": p.adultCount,
                                "childCount": p.childCount,
                                "factor": p.factor,
                                "conditions": p.childCondition_text
                            })
                    # print(childConds)
                    # print(ptds)
                    # print(ptd.factor)
                    # (1, 'Net Fiyat'),
                    # (2, 'Komisyonlu Fiyat'),
                    kontenjan = Quota.objects.filter(otel=i,
                                                     quotaDate__gte=startDate,
                                                     quotaDate__lte=finishDate,
                                                     roomType=acc.roomType.id,
                                                     isActive=True
                                                     ).values_list('quotaDate', flat=True).all()
                    # print('unavailavble days')
                    # print(kontenjan)
                    if kontenjan:
                        f['isPriceAvailable'] = False
                        f['unavailableDays'] = list(kontenjan)
                    else:
                        f['isPriceAvailable'] = True
                        f['unavailableDays'] = []
                    f['childConditions'] = childConds
                    f['priceListByDays'] = priceListByDays
                    # f['numofelement'] = numofelement
                    # f['mindays'] = mindays
                    # f['pricedetails'] = pricedetails
                    # print(acc.currency.name)
                    f['accomodation__roomType'] = acc.roomType.id
                    f['accomodation__roomType__name'] = acc.roomType.name
                    f['accomodation__roomType__name_en'] = acc.roomType.name_en
                    f['accomodation__roomType__name_ru'] = acc.roomType.name_ru
                    f['accomodation__roomType__roomSize'] = acc.roomType.roomSize
                    f['accomodation__roomType__guestCount'] = acc.roomType.guestCount
                    # odaResimleri = OtelImages.objects.filter(roomType=acc.roomType.id)
                    # print('odaResimleri')
                    # print(odaResimleri)

                    odaResimleriDefault = []
                    try:
                        odaImagesDefault = OtelImages.objects.filter(
                            roomType=acc.roomType.id, isDefault=True)
                        # odaImages = OtelImages.objects.filter(roomType=112)
                    except OtelImages.DoesNotExist:
                        odaImagesDefault = None

                    if odaImagesDefault:
                        odaResimleriDefault = list(
                            odaImagesDefault.values('title', 'file').all())

                    f['accomodation__roomType__images_default'] = odaResimleriDefault

                    odaResimleri = []
                    try:
                        odaImages = OtelImages.objects.filter(
                            roomType=acc.roomType.id, isDefault=False)
                        # odaImages = OtelImages.objects.filter(roomType=112)
                    except OtelImages.DoesNotExist:
                        odaImages = None

                    if odaImages:
                        odaResimleri = list(
                            odaImages.values('title', 'file').all())

                    f['accomodation__roomType__images'] = odaResimleri

                    # odaResimleri = []
                    # try:
                    #     odaImages = OtelImages.objects.filter(roomType=acc.roomType.id)
                    #     odaImages = OtelImages.objects.filter(roomType=112)
                    # except OtelImages.DoesNotExist:
                    #     odaImages = None
                    # if odaImages:
                    #     odaResimleri = list(odaImages.values('title', 'file').all())
                    # f['accomodation__roomType__images'] = odaResimleri

                    f['accomodation__pensionType'] = acc.concept.id
                    f['accomodation__pensionType__name'] = acc.concept.name
                    f['accomodation__pensionType__name_en'] = acc.concept.name_en
                    f['accomodation__pensionType__name_ru'] = acc.concept.name_ru
                    f['currency_id'] = acc.currency.id
                    f['currency_name'] = acc.currency.name
                    f['priceFactor'] = facs['factor']
                    # f['roomFeatures'] = list(acc.roomType.feature.values_list('name', flat=True).all())
                    f['roomFeatures'] = list(
                        acc.roomType.feature.values('name', 'iconClassName').all())
                    f['roomFeatures_en'] = list(
                        acc.roomType.feature.values('name_en', 'iconClassName').all())
                    f['roomFeatures_ru'] = list(
                        acc.roomType.feature.values('name_ru', 'iconClassName').all())

                    calcType = acc.priceCalcType
                    kickbackInDates = KickBack.objects.filter(otel_id=i, startDate__lte=startDate,
                                                              finishDate__gte=finishDate,
                                                              isActive=True).values('id',
                                                                                    'amount',
                                                                                    'isKademeliKumulatif').first()
                    print('kickbackInDates')
                    print(kickbackInDates)
                    if kickbackInDates:
                        # print(kickbackInDates['amount'])
                        # print(kickbackInDates['isKademeliKumulatif'])
                        kickbackAmount = kickbackInDates['amount']
                        isKickbackKademeli = kickbackInDates['isKademeliKumulatif']
                    else:
                        kickbackAmount = 0
                        isKickbackKademeli = False

                    actionsInDates = ActionsDetail.objects.filter(
                        (Q(isApplyAllRoomTypes=True) | Q(
                            roomType__in=[f['accomodation__roomType']])),
                        # (Q(actions__id=2) & ~Q(totalDays__lte=len(alldateslist))),
                        (Q(actions__id=1)),
                        otel_id=i,
                        startDate__lte=startDate,
                        finishDate__gte=finishDate,

                        isActive=True).values(
                        # (isApplyAllRoomTypes=True) or (roomType=f['accomodation__roomType'])).values(
                        'id', 'hotelCommission', 'saleDiscount', 'isKademeli', 'fakeRate',
                        'discountRate', 'actions__name', 'actions_id',
                        'isApplyAllRoomTypes', 'roomType',
                        'dayActionCalculation', 'totalDays', 'paidDays', 'minKonaklama',
                        'webDescription').all().distinct('id',
                                                         'actions_id').order_by(
                        'actions_id')
                    # once sartlari uymayan gun aksiyonlarini cikartalim
                    # actionsInDates = actionsInDates.exclude(
                    #     (Q(actions__id=2) & ~Q(minKonaklama__lte=len(alldateslist))))
                    # actionsInDates = actionsInDates.exclude(Q(actions=2))
                    # print('actionsInDates')
                    # print(actionsInDates)

                    f['listPrice'] = listPrice
                    priceListByDays_updated = {}

                    maliyet = listPrice
                    actionsApplied = []
                    if actionsInDates:
                        actionInDate = actionsInDates.first()
                        otherActions = ActionsDetail.objects.get(pk=actionInDate['id']).otherAction.filter(
                            startDate__lte=startDate,
                            finishDate__gte=finishDate,
                            isActive=True).values(
                            'id',
                            'hotelCommission',
                            'saleDiscount',
                            'isKademeli',
                            'fakeRate',
                            'discountRate',
                            'actions__name',
                            'actions_id',
                            'isApplyAllRoomTypes',
                            'roomType',
                            'dayActionCalculation',
                            'totalDays',
                            'paidDays',
                            'minKonaklama',
                            'webDescription').all().distinct('id', 'actions_id')
                        # print(otherActions)
                        otherActions = otherActions.exclude(
                            (Q(actions__id=2) & ~Q(minKonaklama__lte=len(alldateslist))))
                        # print(otherActions.count())
                        # print(otherActions)

                        # otherActions = actionInDate.otherAction.objects.all()
                        # print(actionInDate)
                        hotelCommision = actionInDate['hotelCommission']
                        saleDiscount = actionInDate['saleDiscount']
                        discountRate = actionInDate['discountRate']
                        isAksiyonKademeli = actionInDate['isKademeli']
                        kickbackDiscountAmount = 0
                        if not otherActions:
                            # Eger bagli alt aksiyon yoksa
                            maliyet_old = maliyet
                            maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                maliyet, calcType,
                                isAksiyonKademeli,
                                hotelCommision, discountRate,
                                isKickbackKademeli,
                                kickbackAmount, saleDiscount)
                            for key, value in priceListByDays.items():
                                value_updated, _, _, _, _ = calculateCost(
                                    value, calcType,
                                    isAksiyonKademeli,
                                    hotelCommision, discountRate,
                                    isKickbackKademeli,
                                    0, saleDiscount)
                                priceListByDays_updated[key] = value_updated
                            priceListByDays_updated = dict(
                                sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                       reverse=False))
                            print(" maliyet, afiseFiyat, satisFiyati, karlilik")
                            print(" {:2f}       {:2f}          {:2f}           {:2f} ".format(maliyet, afiseFiyat,
                                                                                              satisFiyati, karlilik))

                            f['maliyet'] = maliyet
                            f['afiseFiyat'] = afiseFiyat
                            f['satisFiyati'] = satisFiyati
                            f['karlilik'] = karlilik
                            f['kickbackTutari'] = kbTutari
                            # maliyet, afiseFiyat, satisFiyati, karlilik)

                            # print(" {} {} {} {} ".format(maliyet, afiseFiyat, satisFiyati,
                            #                              karlilik))
                            actionsApplied.append({
                                "action_id": actionInDate['id'],
                                "action_name": actionInDate['actions__name'],
                                "actionWebDescription": actionInDate['webDescription'],
                                "listPrice": listPrice,
                                "maliyet": maliyet,
                                "afiseFiyat": afiseFiyat,
                                "satisFiyati": satisFiyati,
                                "karlilik": karlilik,
                                "aksiyonIndirimTutari": maliyet_old - maliyet,
                                "aksiyonluFiyatListesi": priceListByDays_updated
                            })
                        else:
                            print('# Eger bagli alt aksiyon(lar) VARSA')
                            for oa in otherActions:
                                print(oa)
                            maliyet_old = maliyet
                            maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                maliyet, calcType,
                                isAksiyonKademeli,
                                hotelCommision, discountRate,
                                isKickbackKademeli,
                                0, saleDiscount)
                            for key, value in priceListByDays.items():
                                value_updated, _, _, _, _ = calculateCost(
                                    value, calcType,
                                    isAksiyonKademeli,
                                    hotelCommision, discountRate,
                                    isKickbackKademeli,
                                    0, saleDiscount)
                                priceListByDays_updated[key] = value_updated
                                # priceListByDays_updated.append(key+'_': value_updated)
                            priceListByDays_updated = dict(
                                sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                       reverse=False))
                            # print(priceListByDays_updated)
                            print(" maliyet, afiseFiyat, satisFiyati, karlilik")
                            print(" {:2f}       {:2f}          {:2f}           {:2f} ".format(maliyet, afiseFiyat,
                                                                                              satisFiyati, karlilik))

                            f['maliyet'] = maliyet
                            f['afiseFiyat'] = afiseFiyat
                            f['satisFiyati'] = satisFiyati
                            f['karlilik'] = karlilik
                            f['kickbackTutari'] = kbTutari

                            # maliyet, afiseFiyat, satisFiyati, karlilik)

                            # print(" {} {} {} {} ".format(maliyet, afiseFiyat, satisFiyati,
                            #                              karlilik))
                            actionsApplied.append({
                                "action_id": actionInDate['id'],
                                "action_name": actionInDate['actions__name'],
                                "actionWebDescription": actionInDate['webDescription'],
                                "listPrice": listPrice,
                                "maliyet": maliyet,
                                "afiseFiyat": afiseFiyat,
                                "satisFiyati": satisFiyati,
                                "karlilik": karlilik,
                                "aksiyonIndirimTutari": maliyet_old - maliyet,
                                "aksiyonluFiyatListesi": priceListByDays_updated
                            })
                            actionslist_len = len(otherActions)
                            for index, acid in enumerate(otherActions):
                                print('actions_id')
                                print(acid['actions_id'])
                                if acid['actions_id'] == 2:
                                    # gun aksyionu
                                    unpaidDays = acid['minKonaklama'] - \
                                        acid['paidDays']
                                    discountAmount = unpaidDays * \
                                        (list(
                                            priceListByDays_updated.values())[0])
                                    print("Gun aksyionu uygulaniyor [Indirim tutari= {}]".format(
                                        discountAmount))
                                    maliyet_old = maliyet
                                    maliyet -= discountAmount
                                    afiseFiyat -= discountAmount
                                    satisFiyati -= discountAmount

                                    if index == actionslist_len - 1:
                                        maliyet_old = maliyet
                                        maliyet = maliyet * \
                                            (1 - kickbackAmount / 100)
                                        afiseFiyat = afiseFiyat * \
                                            (1 - kickbackAmount / 100)
                                        satisFiyati = satisFiyati * \
                                            (1 - kickbackAmount / 100)
                                        print(' KICKback uygulandi {:2f}'.format(
                                            kickbackAmount))

                                    karlilik = (
                                        satisFiyati - maliyet) / satisFiyati
                                    # karlilik = (satisFiyati - maliyet) /

                                    maliyet = round(maliyet, 2)
                                    afiseFiyat = round(afiseFiyat, 2)
                                    satisFiyati = round(satisFiyati, 2)
                                    karlilik = round(karlilik * 100, 2)
                                    # f['kickbackAmount'] = maliyet_old - maliyet

                                if acid['actions_id'] in [3, 4, 5, 6]:
                                    print('Genel aksiyon uygulandi..')
                                    hotelCommision = acid['hotelCommission']
                                    saleDiscount = acid['saleDiscount']
                                    discountRate = acid['discountRate']
                                    isAksiyonKademeli = acid['isKademeli']

                                    if index == actionslist_len - 1:
                                        maliyet_old = maliyet
                                        maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                            maliyet, calcType,
                                            isAksiyonKademeli,
                                            hotelCommision, discountRate,
                                            isKickbackKademeli,
                                            kickbackAmount, saleDiscount)
                                        f['kickbackAmount'] = maliyet_old - maliyet
                                        for key, value in priceListByDays.items():
                                            value_updated, _, _, _, _ = calculateCost(
                                                value, calcType,
                                                isAksiyonKademeli,
                                                hotelCommision, discountRate,
                                                isKickbackKademeli,
                                                0, saleDiscount)
                                            priceListByDays_updated[key] = value_updated
                                        priceListByDays_updated = dict(
                                            sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                                   reverse=False))
                                    else:
                                        maliyet, afiseFiyat, satisFiyati, karlilik, kbTutari = calculateCost(
                                            maliyet, calcType,
                                            isAksiyonKademeli,
                                            hotelCommision, discountRate,
                                            isKickbackKademeli,
                                            0, saleDiscount)
                                        for key, value in priceListByDays.items():
                                            value_updated, _, _, _, kbTutari = calculateCost(
                                                value, calcType,
                                                isAksiyonKademeli,
                                                hotelCommision, discountRate,
                                                isKickbackKademeli,
                                                0, saleDiscount)
                                            priceListByDays_updated[key] = value_updated
                                            # priceListByDays_updated.append(key+'_': value_updated)
                                        priceListByDays_updated = dict(
                                            sorted(priceListByDays_updated.items(), key=operator.itemgetter(1),
                                                   reverse=False))

                                actionsApplied.append({
                                    "action_id": acid['id'],
                                    "action_name": acid['actions__name'],
                                    "actionWebDescription": acid['webDescription'],
                                    "listPrice": listPrice,
                                    "maliyet": maliyet,
                                    "afiseFiyat": afiseFiyat,
                                    "satisFiyati": satisFiyati,
                                    "karlilik": karlilik,
                                    "aksiyonIndirimTutari": maliyet_old - maliyet,
                                    "aksiyonluFiyatListesi": priceListByDays_updated
                                })

                            # print('actionslist_len')
                            # print(actionslist_len)
                            #
                            # for oa in otherActions:
                            #     print(oa)

                    else:
                        print('no actions get contract')
                        c = Contract.objects.filter(otel_id=i, startDate__lte=startDate,
                                                    finishDate__gte=finishDate,
                                                    isActive=True).values('id',
                                                                          'commissionRate').order_by(
                            'id').last()
                        print(c)

                        f['acc_id'] = 0
                        f['maliyet'] = 0
                        f['afiseFiyat'] = 0
                        f['satisFiyati'] = 0
                        f['karlilik'] = 0
                    f['actionsApplied'] = actionsApplied
                    # print(f)

                if f:
                    priceItem['priceItems'].append(f)
                    resultCount += 1
            if len(priceItem['priceItems']) > 0:
                response["prices"].append(priceItem)
        response['otelsFound'] = len(response["prices"])
        response['pricesFound'] = resultCount

        return Response(response)


class UploadImage(LoggingMixin, CreateAPIView):
    serializer_class = serializers.Serializer

    def post(self, request, **kwargs):
        images = request.data['images']
        response = {}
        for i in images:
            data = i['file']
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            # You can save this as file instance.
            imgfile = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
            otelimage = {
                "title": i['title'],
                "description": i['description'],
                "file": imgfile,
                "processType": i['processType'],
                "isVideo": i['isVideo'],
                "otel": i['otel'],
                "imageCategory": i['imageCategory'],
                "roomType": i['roomType']
            }
            isError = False
            img = OtelImagesSerializer(data=otelimage)
            if img.is_valid():
                img.save()
            else:
                # print(img.errors)
                isError = True
                break
        if isError:
            response = {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": img.errors
            }
        else:
            response = {
                "status": status.HTTP_201_CREATED,
                "message": "Images created succesfully"
            }
        return Response(response)


class ModulePaymentAccountInfoAnonim(LoggingMixin, ListAPIView):
    # this api will be anonimous and implemnent GET/Retrieve only
    authentication_classes = []
    permission_classes = []
    serializer_class = PaymentAccountInfoGetSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel': ['exact'],
    }
    search_fields = ('id', 'otel')
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PaymentAccountInfo.objects.filter(isActive=True)
        return queryset


class PayAtFacilityAnonimList(LoggingMixin, ListAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = PayAtFacilityGetSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'contract__otel': ['exact'],
        'startDate': ['gte', 'lte', 'exact'],
        'finishDate': ['gte', 'lte', 'exact'],
    }
    search_fields = ('id',)
    ordering_fields = '__all__'
    ordering = ['-id']
    #    permission_classes = [IsAuthenticated]
    pagination_class = OtelPagination

    def get_queryset(self):
        queryset = PayAtFacility.objects.filter(isActive=True).order_by('id')
        return queryset


class CheckPriceStatus(APIView):

    """This api requires otelId in payload and returns otel price status"""

    def post(self, request, *args, **kwargs):
        otelId = request.data["otelId"]
        otelPriceStatus = Otel.objects.get(id=otelId).priceStatus
        recordCount = BrokenPrice.objects.filter(otel__id=otelId).count()
        responseData = {
            "priceStatus": otelPriceStatus,
            "recordCount": recordCount
        }

        return Response(responseData)


class BrokenPriceList(ListAPIView, CreateModelMixin):
    serializer_class = BrokenPriceSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter)
    filterset_fields = {
        'id': ['exact'],
        'otel__id': ['exact'],
    }
    search_fields = ('id', )
    ordering = ['-id']

    def get_queryset(self):
        queryset = BrokenPrice.objects.filter(isActive=True)
        return queryset

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = BrokenPriceSerializer(
            data=request.data, many=many)
        if serializer.is_valid():
            with transaction.atomic():
                for requestData in request.data:
                    BrokenPrice.objects.filter(
                        otel__id=requestData["otel"]).delete()
                serializer.save(createdBy=self.request.user,
                                updatedBy=self.request.user)
                for requestData in request.data:
                    Otel.objects.filter(id=requestData["otel"]).update(
                        priceStatus=True)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        otelId = self.request.query_params["otel__id"]
        brokenPrices = list(BrokenPrice.objects.filter(
            otel__id=otelId, isActive=True))
        roomTypeNameList = []
        pensionTypeNameList = []
        responseData = response.data
        for brokenPrice in brokenPrices:
            if brokenPrice.roomType != None:
                if brokenPrice.roomType.name not in roomTypeNameList:
                    roomTypeNameList.append(brokenPrice.roomType.name)
            if brokenPrice.pensionType != None:
                if brokenPrice.pensionType.name not in pensionTypeNameList:
                    pensionTypeNameList.append(brokenPrice.pensionType.name)
        responseData["roomTypeNameList"] = roomTypeNameList
        responseData["pensionTypeNameList"] = pensionTypeNameList
        return Response(responseData)


class BrokenPriceChange(DestroyAPIView, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = BrokenPrice.objects.filter(isActive=True)
    serializer_class = BrokenPriceSerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(updatedBy=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class ReservationSearch(APIView):
    """
    It takes startDate, endDate, otelIdList, roomCount, adultCount, childCount, stayDayCount
    And Returns available reservation list from Quota table
    """

    def post(self, request, *args, **kwargs):
        startDate = request.data['startDate']
        endDate = request.data["endDate"]
        otelIdList = request.data["otelIdList"]
        roomCount = request.data["roomCount"]
        adultCount = request.data["adultCount"]
        childCount = request.data["childCount"]
        stayDayCount = request.data["stayDayCount"]
        childAges = request.data["childAges"]

        # First filter the Quota table up to payload data
        filteredQuotaList = list(Quota.objects.filter(
            quotaDate__gte=startDate, quotaDate__lt=endDate, quota__gte=roomCount, otel__id__in=otelIdList, isActive=True).values("id", "otel__id", "otel__name", "otel__region__name", "otel__subRegion__name", "otel__location__name", "roomType__id", "roomType__name", "quotaDate", "quota", "status").distinct("roomType__id"))

        # Now it is time to filter the BrokenPrice
        # For each filteredQuotaList, it will be filtered up to roomType_id
        brokenPriceList = []
        for filteredQuota in filteredQuotaList:
            brokenPrices = list(BrokenPrice.objects.filter(otel__id=filteredQuota["otel__id"], roomType__id=filteredQuota["roomType__id"], totalMinDays__lte=stayDayCount,
                                totalMaxDays__gte=stayDayCount, saleStartDate__lte=datetime.now(), saleEndDate__gte=datetime.now()).values())
            for eachBrokenPrice in brokenPrices:
                brokenPriceList.append(eachBrokenPrice)

        # divide brokenprices according to module
        priceBrokenPrices = list(filter(
            lambda brokenPrice: brokenPrice["module"] == 1, brokenPriceList))
        actionBrokenPrices = list(filter(
            lambda brokenPrice: brokenPrice["module"] == 2, brokenPriceList))

        # get child conditions and factor from priceDetail
        for priceBrokenPrice in priceBrokenPrices:
            priceDetails = list(PriceDetails.objects.filter(adultCount=adultCount, childCount=childCount,
                                otel__id=priceBrokenPrice["otel_id"], priceTemplate__id=priceBrokenPrice["priceTemplateId"]).values("id", "childCondition", "factor"))
            for priceDetail in priceDetails:
                priceBrokenPrice["childCondition"] = priceDetail["childCondition"]
                priceBrokenPrice["factor"] = priceDetail["factor"]

        # get child conditions and factor from actionPriceDetail
        for actionBrokenPrice in actionBrokenPrices:
            actionPriceDetails = list(ActionPriceDetail.objects.filter(adultCount=adultCount, childCount=childCount,
                                                                       action__otel__id=actionBrokenPrice["otel_id"], priceTemplate__id=actionBrokenPrice["priceTemplateId"]).values("id", "childCondition", "factor"))
            for actionPriceDetail in actionPriceDetails:
                actionBrokenPrice["childCondition"] = actionPriceDetail["childCondition"]
                actionBrokenPrice["factor"] = actionPriceDetail["factor"]

        # get lastPriceBrokenPriceList according to child conditions
        lastPriceBrokenPriceList = []
        if childAges == []:
            for eachPriceBrokenPrice in priceBrokenPrices:
                lastPriceBrokenPriceList.append(eachPriceBrokenPrice)
        else:
            for eachPriceBrokenPrice in priceBrokenPrices:
                childConditions = []
                if eachPriceBrokenPrice["childCondition"] == None:
                    continue
                for eachChildConditionId in eachPriceBrokenPrice["childCondition"]:
                    if ChildCondition.objects.get(id=eachChildConditionId).isActive == False:
                        continue
                    childConditionValues = {
                        "id": ChildCondition.objects.get(id=eachChildConditionId).id,
                        "startAge": ChildCondition.objects.get(id=eachChildConditionId).startAge,
                        "finishAge": ChildCondition.objects.get(id=eachChildConditionId).finishAge,
                    }
                    childConditions.append(childConditionValues)
                if (childConditions == []) or (childConditions == None):
                    pass
                else:
                    foundChildConditionList = []
                    for childAge in childAges:
                        for childConditionIndex in range(len(childConditions)):
                            if childConditions[childConditionIndex]["startAge"] <= childAge <= childConditions[childConditionIndex]["finishAge"]:
                                if childConditionIndex not in foundChildConditionList:
                                    foundChildConditionList.append(
                                        childConditionIndex)
                                    break
                    if len(foundChildConditionList) == childCount:
                        lastPriceBrokenPriceList.append(eachPriceBrokenPrice)

        # get lastActionBrokenPrice according to childconditions
        lastActionBrokenPriceList = []
        if childAges == []:
            for eachActionBrokenPrice in actionBrokenPrices:
                lastActionBrokenPriceList.append(eachActionBrokenPrice)
        else:
            for eachActionBrokenPrice in actionBrokenPrices:
                childConditions = []
                if eachActionBrokenPrice["childCondition"] == None:
                    continue
                for eachChildConditionId in eachActionBrokenPrice["childCondition"]:
                    if ChildCondition.objects.get(id=eachChildConditionId).isActive == False:
                        continue
                    childConditionValues = {
                        "id": ChildCondition.objects.get(id=eachChildConditionId).id,
                        "startAge": ChildCondition.objects.get(id=eachChildConditionId).startAge,
                        "finishAge": ChildCondition.objects.get(id=eachChildConditionId).finishAge,
                    }
                    childConditions.append(childConditionValues)
                if (childConditions == []) or (childConditions == None):
                    pass
                else:
                    foundChildConditionList = []
                    for childAge in childAges:
                        for childConditionIndex in range(len(childConditions)):
                            if childConditions[childConditionIndex]["startAge"] <= childAge <= childConditions[childConditionIndex]["finishAge"]:
                                if childConditionIndex not in foundChildConditionList:
                                    foundChildConditionList.append(
                                        childConditionIndex)
                                    break
                    if len(foundChildConditionList) == childCount:
                        lastActionBrokenPriceList.append(eachActionBrokenPrice)

        for lastPriceBrokenPrice in lastPriceBrokenPriceList:
            if lastPriceBrokenPrice["priceMinDays"] == None:
                lastPriceBrokenPrice["priceMinDays"] = 0

        for lastActionBrokenPrice in lastActionBrokenPriceList:
            if lastActionBrokenPrice["priceMinDays"] == None:
                lastActionBrokenPrice["priceMinDays"] = 0

        sortedPriceBrokenPriceList = sorted(
            lastPriceBrokenPriceList, key=lambda k: k["priceMinDays"], reverse=True)
        sortedActionBrokenPriceList = sorted(
            lastActionBrokenPriceList, key=lambda k: k["priceMinDays"], reverse=True)

        # get stayDateWeekDays in a list to compare it with related Price
        stayDateWeekDayList = []
        for i in range(stayDayCount):
            stayDate = (datetime.strptime(str(startDate), '%Y-%m-%d') +
                        timedelta(days=i)).strftime('%Y-%m-%d')
            stayDateWeekDay = datetime.strptime(
                str(stayDate), '%Y-%m-%d').weekday() + 1
            stayDateWeekDayList.append(stayDateWeekDay)

        # get needed brokenprices
        finalPriceBrokenPriceList = []
        for sortedPriceBrokenPrice in sortedPriceBrokenPriceList:
            priceDayIntersection = list(set(stayDateWeekDayList).intersection(
                sortedPriceBrokenPrice["priceDays"]))
            if len(priceDayIntersection) >= sortedPriceBrokenPrice["priceMinDays"]:
                finalPriceBrokenPriceList.append(sortedPriceBrokenPrice)
            else:
                sortedPriceBrokenPriceList.remove(sortedPriceBrokenPrice)

        # remove unnecessary prices
        for finalPriceBrokenPrice in finalPriceBrokenPriceList:
            for sortedPriceBrokenPrice in sortedPriceBrokenPriceList:
                if finalPriceBrokenPrice["otel_id"] == sortedPriceBrokenPrice["otel_id"]:
                    if finalPriceBrokenPrice["roomType_id"] == sortedPriceBrokenPrice["roomType_id"]:
                        if finalPriceBrokenPrice["pensionType_id"] == sortedPriceBrokenPrice["pensionType_id"]:
                            if finalPriceBrokenPrice["priceDays"] == sortedPriceBrokenPrice["priceDays"]:
                                if finalPriceBrokenPrice["priceMinDays"] < sortedPriceBrokenPrice["priceMinDays"]:
                                    if finalPriceBrokenPrice in finalPriceBrokenPriceList:
                                        finalPriceBrokenPriceList.remove(
                                            finalPriceBrokenPrice)

        # get needed actionbrokenprices
        finalActionBrokenPriceList = []
        for sortedActionBrokenPrice in sortedActionBrokenPriceList:
            actionPriceDayIntersection = list(set(stayDateWeekDayList).intersection(
                sortedActionBrokenPrice["priceDays"]))
            if len(actionPriceDayIntersection) >= sortedActionBrokenPrice["priceMinDays"]:
                finalActionBrokenPriceList.append(sortedActionBrokenPrice)
            else:
                sortedActionBrokenPriceList.remove(sortedActionBrokenPrice)

        # remove unnecessary actionprices
        for finalActionBrokenPrice in finalActionBrokenPriceList:
            for sortedActionBrokenPrice in sortedActionBrokenPriceList:
                if finalActionBrokenPrice["otel_id"] == sortedActionBrokenPrice["otel_id"]:
                    if finalActionBrokenPrice["roomType_id"] == sortedActionBrokenPrice["roomType_id"]:
                        if finalActionBrokenPrice["pensionType_id"] == sortedActionBrokenPrice["pensionType_id"]:
                            if finalActionBrokenPrice["priceDays"] == sortedActionBrokenPrice["priceDays"]:
                                if finalActionBrokenPrice["priceMinDays"] < sortedActionBrokenPrice["priceMinDays"]:
                                    if finalActionBrokenPrice in finalActionBrokenPriceList:
                                        finalActionBrokenPriceList.remove(
                                            finalActionBrokenPrice)

        # get needed actionBrokenPrices and calculate new
        # dictionary List to calculate price
        actionDict = {}
        actionDictList = []
        for finalActionBrokenPrice in finalActionBrokenPriceList:
            if finalActionBrokenPrice["base"] == 1:
                if finalActionBrokenPrice["accomodationStartDate"] <= datetime.strptime(str(startDate), '%Y-%m-%d').date():
                    actionStartDateWeekDay = datetime.strptime(
                        str(finalActionBrokenPrice["accomodationStartDate"]), '%Y-%m-%d').weekday() + 1
                    if actionStartDateWeekDay in finalActionBrokenPrice["priceDays"]:
                        for a in range(stayDayCount):
                            actionStayDate = ((datetime.strptime(
                                str(startDate), '%Y-%m-%d') + timedelta(days=a)).strftime('%Y-%m-%d'))
                            # convert stayDate to date format to compare with accomodation startDate and finishDate
                            actionStayDate = datetime.strptime(
                                str(actionStayDate), '%Y-%m-%d').date()
                            actionDict = {
                                "otelId": finalActionBrokenPrice["otel_id"],
                                "roomTypeId": finalActionBrokenPrice["roomType_id"],
                                "pensionTypeId": finalActionBrokenPrice["pensionType_id"],
                                "stayDate": actionStayDate,
                                "perPersonPrice": finalActionBrokenPrice["perPersonPrice"],
                                "base": finalActionBrokenPrice["base"],
                                "priceCalcType": finalActionBrokenPrice["priceCalcType"],
                                "profitMargin": finalActionBrokenPrice["profitMargin"],
                                "posterDiscountRate": finalActionBrokenPrice["posterDiscountRate"],
                                "factor": finalActionBrokenPrice["factor"],
                                "salePrice": finalActionBrokenPrice["salePrice"]*finalActionBrokenPrice["factor"],
                                "posterPrice": finalActionBrokenPrice["posterPrice"]*finalActionBrokenPrice["factor"],
                                "ebBase": finalActionBrokenPrice["ebBase"],
                                "ebRate": finalActionBrokenPrice["ebRate"],
                                "ebComissionType": finalActionBrokenPrice["ebComissionType"],
                                "spoBase": finalActionBrokenPrice["spoBase"],
                                "spoRate": finalActionBrokenPrice["spoRate"],
                                "spoComissionType": finalActionBrokenPrice["spoComissionType"],
                            }
                            actionDictList.append(actionDict)
                        if finalActionBrokenPrice["ebBase"] == 2:
                            for action in actionDictList:
                                for ebFinalActionBrokenPrice in finalActionBrokenPriceList:
                                    if action["otelId"] == ebFinalActionBrokenPrice["otel_id"]:
                                        if action["roomTypeId"] == ebFinalActionBrokenPrice["roomType_id"]:
                                            if action["pensionTypeId"] == ebFinalActionBrokenPrice["pensionType_id"]:
                                                if ebFinalActionBrokenPrice["accomodationStartDate"] <= action["stayDate"] <= ebFinalActionBrokenPrice["accomodationEndDate"]:
                                                    action["ebComissionType"] = ebFinalActionBrokenPrice["ebComissionType"]
                                                    action["ebRate"] = ebFinalActionBrokenPrice["ebRate"]
                                                    action["profitMargin"] = ebFinalActionBrokenPrice["profitMargin"]
                                                    action["posterDiscountRate"] = ebFinalActionBrokenPrice["posterDiscountRate"]
                                                    if action["priceCalcType"] == 1:
                                                        if action["ebRate"] == None:
                                                            action["ebRate"] = 0
                                                        if action["profitMargin"] == None:
                                                            action["profitMargin"] = 0
                                                        if action["posterDiscountRate"] == None:
                                                            action["posterDiscountRate"] = 0
                                                        action["salePrice"] = action["perPersonPrice"] * \
                                                            action["factor"]
                                                        action["salePrice"] -= (
                                                            action["salePrice"]*action["ebRate"]/100)
                                                        action["salePrice"] += (
                                                            action["salePrice"]*action["profitMargin"]/100)
                                                        action["posterPrice"] = action["salePrice"] + (
                                                            action["salePrice"]*action["posterDiscountRate"]/100)
                                                    elif action["priceCalcType"] == 2:
                                                        action["posterPrice"] = action["perPersonPrice"] * \
                                                            action["factor"]
                                                        action["salePrice"] = action["posterPrice"] - (
                                                            action["posterPrice"]*action["posterDiscountRate"]/100)

                        elif finalActionBrokenPrice["spoBase"] == 2:
                            for action in actionDictList:
                                for spoFinalActionBrokenPrice in finalActionBrokenPriceList:
                                    if action["otelId"] == spoFinalActionBrokenPrice["otel_id"]:
                                        if action["roomTypeId"] == spoFinalActionBrokenPrice["roomType_id"]:
                                            if action["pensionTypeId"] == spoFinalActionBrokenPrice["pensionType_id"]:
                                                if spoFinalActionBrokenPrice["accomodationStartDate"] <= action["stayDate"] <= spoFinalActionBrokenPrice["accomodationEndDate"]:
                                                    action["spoComissionType"] = spoFinalActionBrokenPrice["spoComissionType"]
                                                    action["spoRate"] = spoFinalActionBrokenPrice["ebRate"]
                                                    action["profitMargin"] = spoFinalActionBrokenPrice["profitMargin"]
                                                    action["posterDiscountRate"] = spoFinalActionBrokenPrice["posterDiscountRate"]
                                                    if action["priceCalcType"] == 1:
                                                        if action["ebRate"] == None:
                                                            action["ebRate"] = 0
                                                        if action["spoRate"] == None:
                                                            action["spoRate"] = 0
                                                        if action["profitMargin"] == None:
                                                            action["profitMargin"] = 0
                                                        if action["posterDiscountRate"] == None:
                                                            action["posterDiscountRate"] = 0
                                                        if action["spoComissionType"] == 1:
                                                            action["salePrice"] = action["perPersonPrice"] * \
                                                                action["factor"]
                                                            action["salePrice"] -= (
                                                                action["salePrice"]*action["ebRate"]/100)
                                                            action["salePrice"] -= (
                                                                action["salePrice"]*action["spoRate"]/100)
                                                            action["salePrice"] += (
                                                                action["salePrice"]*action["profitMargin"]/100)
                                                            action["posterPrice"] = action["salePrice"] + (
                                                                action["salePrice"]*action["posterDiscountRate"]/100)
                                                        elif action["spoComissionType"] == 2:
                                                            totalDiscountRate = action["ebRate"] + \
                                                                action["spoRate"]
                                                            action["salePrice"] = action["perPersonPrice"] * \
                                                                action["factor"]
                                                            action["salePrice"] -= (
                                                                action["salePrice"]*totalDiscountRate/100)
                                                            action["salePrice"] += (
                                                                action["salePrice"]*action["profitMargin"]/100)
                                                            action["posterPrice"] = action["salePrice"] + (
                                                                action["salePrice"]*action["posterDiscountRate"]/100)
                                                    elif action["priceCalcType"] == 2:
                                                        action["posterPrice"] = action["perPersonPrice"] * \
                                                            action["factor"]
                                                        action["salePrice"] = action["posterPrice"] - (
                                                            action["posterPrice"]*action["posterDiscountRate"]/100)
            elif finalActionBrokenPrice["base"] == 2:
                for b in range(stayDayCount):
                    actionAccomodationStayDate = ((datetime.strptime(
                        str(startDate), '%Y-%m-%d') + timedelta(days=b)).strftime('%Y-%m-%d'))
                    # convert stayDate to date format to compare with accomodation startDate and finishDate
                    actionAccomodationStayDate = datetime.strptime(
                        str(actionAccomodationStayDate), '%Y-%m-%d').date()
                    actionAccomodationStayDateWeekDay = datetime.strptime(
                        str(actionAccomodationStayDate), '%Y-%m-%d').weekday() + 1
                    if finalActionBrokenPrice["accomodationStartDate"] <= actionAccomodationStayDate <= finalActionBrokenPrice["accomodationEndDate"]:
                        if actionAccomodationStayDateWeekDay in finalActionBrokenPrice["priceDays"]:
                            actionDict = {
                                "otelId": finalActionBrokenPrice["otel_id"],
                                "roomTypeId": finalActionBrokenPrice["roomType_id"],
                                "pensionTypeId": finalActionBrokenPrice["pensionType_id"],
                                "stayDate": actionAccomodationStayDate,
                                "perPersonPrice": finalActionBrokenPrice["perPersonPrice"],
                                "base": finalActionBrokenPrice["base"],
                                "priceCalcType": finalActionBrokenPrice["priceCalcType"],
                                "profitMargin": finalActionBrokenPrice["profitMargin"],
                                "posterDiscountRate": finalActionBrokenPrice["posterDiscountRate"],
                                "factor": finalActionBrokenPrice["factor"],
                                "salePrice": finalActionBrokenPrice["salePrice"]*finalActionBrokenPrice["factor"],
                                "posterPrice": finalActionBrokenPrice["posterPrice"]*finalActionBrokenPrice["factor"],
                                "ebBase": finalActionBrokenPrice["ebBase"],
                                "ebRate": finalActionBrokenPrice["ebRate"],
                                "ebComissionType": finalActionBrokenPrice["ebComissionType"],
                                "spoBase": finalActionBrokenPrice["spoBase"],
                                "spoRate": finalActionBrokenPrice["spoRate"],
                                "spoComissionType": finalActionBrokenPrice["spoComissionType"],
                            }
                            actionDictList.append(actionDict)
                if finalActionBrokenPrice["ebBase"] == 1:
                    for action in actionDictList:
                        if action["otelId"] == finalActionBrokenPrice["otel_id"]:
                            if action["roomTypeId"] == finalActionBrokenPrice["roomType_id"]:
                                if action["pensionTypeId"] == finalActionBrokenPrice["pensionType_id"]:
                                    if finalActionBrokenPrice["accomodationStartDate"] <= datetime.strptime(str(startDate), '%Y-%m-%d').date():
                                        action["ebComissionType"] = finalActionBrokenPrice["ebComissionType"]
                                        action["ebRate"] = finalActionBrokenPrice["ebRate"]
                                        action["profitMargin"] = finalActionBrokenPrice["profitMargin"]
                                        action["posterDiscountRate"] = finalActionBrokenPrice["posterDiscountRate"]
                                        if action["priceCalcType"] == 1:
                                            if action["ebRate"] == None:
                                                action["ebRate"] = 0
                                            if action["profitMargin"] == None:
                                                action["profitMargin"] = 0
                                            if action["posterDiscountRate"] == None:
                                                action["posterDiscountRate"] = 0
                                            action["salePrice"] = action["perPersonPrice"] * \
                                                action["factor"]
                                            action["salePrice"] -= (
                                                action["salePrice"]*action["ebRate"]/100)
                                            action["salePrice"] += (
                                                action["salePrice"]*action["profitMargin"]/100)
                                            action["posterPrice"] = action["salePrice"] + (
                                                action["salePrice"]*action["posterDiscountRate"]/100)
                                        elif action["priceCalcType"] == 2:
                                            action["posterPrice"] = action["perPersonPrice"] * \
                                                action["factor"]
                                            action["salePrice"] = action["posterPrice"] - (
                                                action["posterPrice"]*action["posterDiscountRate"]/100)

                elif finalActionBrokenPrice["spoBase"] == 1:
                    for action in actionDictList:
                        if action["otelId"] == finalActionBrokenPrice["otel_id"]:
                            if action["roomTypeId"] == finalActionBrokenPrice["roomType_id"]:
                                if action["pensionTypeId"] == finalActionBrokenPrice["pensionType_id"]:
                                    if finalActionBrokenPrice["accomodationStartDate"] <= datetime.strptime(str(startDate), '%Y-%m-%d').date():
                                        action["spoComissionType"] = finalActionBrokenPrice["spoComissionType"]
                                        action["spoRate"] = finalActionBrokenPrice["spoRate"]
                                        action["profitMargin"] = finalActionBrokenPrice["profitMargin"]
                                        action["posterDiscountRate"] = finalActionBrokenPrice["posterDiscountRate"]
                                        if action["priceCalcType"] == 1:
                                            if action["ebRate"] == None:
                                                action["ebRate"] = 0
                                            if action["spoRate"] == None:
                                                action["spoRate"] = 0
                                            if action["profitMargin"] == None:
                                                action["profitMargin"] = 0
                                            if action["posterDiscountRate"] == None:
                                                action["posterDiscountRate"] = 0
                                            if action["spoComissionType"] == 1:
                                                action["salePrice"] = action["perPersonPrice"] * \
                                                    action["factor"]
                                                action["salePrice"] -= (
                                                    action["salePrice"]*action["ebRate"]/100)
                                                action["salePrice"] -= (
                                                    action["salePrice"]*action["spoRate"]/100)
                                                action["salePrice"] += (
                                                    action["salePrice"]*action["profitMargin"]/100)
                                                action["posterPrice"] = action["salePrice"] + (
                                                    action["salePrice"]*action["posterDiscountRate"]/100)
                                            elif action["spoComissionType"] == 2:
                                                totalDiscountRate = action["ebRate"] + \
                                                    action["spoRate"]
                                                action["salePrice"] = action["perPersonPrice"] * \
                                                    action["factor"]
                                                action["salePrice"] -= (
                                                    action["perPersonPrice"]*totalDiscountRate/100)
                                                action["salePrice"] += (
                                                    action["salePrice"]*action["profitMargin"]/100)
                                                action["posterPrice"] = action["salePrice"] + (
                                                    action["salePrice"]*action["posterDiscountRate"]/100)
                                        elif action["priceCalcType"] == 2:
                                            action["posterPrice"] = action["perPersonPrice"] * \
                                                action["factor"]
                                            action["salePrice"] = action["posterPrice"] - (
                                                action["posterPrice"]*action["posterDiscountRate"]/100)

        # get needed actionBrokenPrices and calculate new
        # dictionary List to calculate price
        priceDict = {}
        priceDictList = []
        for finalPriceBrokenPrice in finalPriceBrokenPriceList:
            if finalPriceBrokenPrice["base"] == 2:
                for c in range(stayDayCount):
                    priceStayDate = ((datetime.strptime(
                        str(startDate), '%Y-%m-%d') + timedelta(days=c)).strftime('%Y-%m-%d'))
                    # convert stayDate to date format to compare with accomodation startDate and finishDate
                    priceStayDate = datetime.strptime(
                        str(priceStayDate), '%Y-%m-%d').date()
                    priceStayDateWeekDay = datetime.strptime(
                        str(priceStayDate), '%Y-%m-%d').weekday() + 1
                    if finalPriceBrokenPrice["accomodationStartDate"] <= priceStayDate <= finalPriceBrokenPrice["accomodationEndDate"]:
                        if priceStayDateWeekDay in finalPriceBrokenPrice["priceDays"]:
                            priceDict = {
                                "otelId": finalPriceBrokenPrice["otel_id"],
                                "roomTypeId": finalPriceBrokenPrice["roomType_id"],
                                "pensionTypeId": finalPriceBrokenPrice["pensionType_id"],
                                "stayDate": priceStayDate,
                                "perPersonPrice": finalPriceBrokenPrice["perPersonPrice"],
                                "base": finalPriceBrokenPrice["base"],
                                "priceCalcType": finalPriceBrokenPrice["priceCalcType"],
                                "profitMargin": finalPriceBrokenPrice["profitMargin"],
                                "posterDiscountRate": finalPriceBrokenPrice["posterDiscountRate"],
                                "factor": finalPriceBrokenPrice["factor"],
                                "salePrice": finalPriceBrokenPrice["salePrice"]*finalPriceBrokenPrice["factor"],
                                "posterPrice": finalPriceBrokenPrice["posterPrice"]*finalPriceBrokenPrice["factor"],
                                "ebBase": finalPriceBrokenPrice["ebBase"],
                                "ebRate": finalPriceBrokenPrice["ebRate"],
                                "ebComissionType": finalPriceBrokenPrice["ebComissionType"],
                                "spoBase": finalPriceBrokenPrice["spoBase"],
                                "spoRate": finalPriceBrokenPrice["spoRate"],
                                "spoComissionType": finalPriceBrokenPrice["spoComissionType"],
                            }
                            priceDictList.append(priceDict)
                if finalPriceBrokenPrice["ebBase"] == 1:
                    for price in priceDictList:
                        if price["otelId"] == finalPriceBrokenPrice["otel_id"]:
                            if price["roomTypeId"] == finalPriceBrokenPrice["roomType_id"]:
                                if price["pensionTypeId"] == finalPriceBrokenPrice["pensionType_id"]:
                                    if finalPriceBrokenPrice["accomodationStartDate"] <= price["stayDate"] <= finalPriceBrokenPrice["accomodationEndDate"]:
                                        price["ebComissionType"] = finalPriceBrokenPrice["ebComissionType"]
                                        price["ebRate"] = finalPriceBrokenPrice["ebRate"]
                                        price["profitMargin"] = finalPriceBrokenPrice["profitMargin"]
                                        price["posterDiscountRate"] = finalPriceBrokenPrice["posterDiscountRate"]
                                        if price["priceCalcType"] == 1:
                                            if price["ebRate"] == None:
                                                price["ebRate"] = 0
                                            if price["profitMargin"] == None:
                                                price["profitMargin"] = 0
                                            if price["posterDiscountRate"] == None:
                                                price["posterDiscountRate"] = 0
                                            price["salePrice"] = price["perPersonPrice"] * \
                                                price["factor"]
                                            price["salePrice"] -= (
                                                price["salePrice"]*price["ebRate"]/100)
                                            price["salePrice"] += (
                                                price["salePrice"]*price["profitMargin"]/100)
                                            price["posterPrice"] = price["salePrice"] + (
                                                price["salePrice"]*price["posterDiscountRate"]/100)
                                        elif price["priceCalcType"] == 2:
                                            price["posterPrice"] = price["perPersonPrice"] * \
                                                price["factor"]
                                            price["salePrice"] = price["posterPrice"] - (
                                                price["posterPrice"]*price["posterDiscountRate"]/100)

                elif finalPriceBrokenPrice["spoBase"] == 1:
                    for price in priceDictList:
                        if price["otelId"] == finalPriceBrokenPrice["otel_id"]:
                            if price["roomTypeId"] == finalPriceBrokenPrice["roomType_id"]:
                                if price["pensionTypeId"] == finalPriceBrokenPrice["pensionType_id"]:
                                    if finalPriceBrokenPrice["accomodationStartDate"] <= price["stayDate"] <= finalPriceBrokenPrice["accomodationEndDate"]:
                                        price["spoComissionType"] = finalPriceBrokenPrice["spoComissionType"]
                                        price["spoRate"] = finalPriceBrokenPrice["spoRate"]
                                        price["profitMargin"] = finalPriceBrokenPrice["profitMargin"]
                                        if price["priceCalcType"] == 1:
                                            if price["ebRate"] == None:
                                                price["ebRate"] = 0
                                            if price["spoRate"] == None:
                                                price["spoRate"] = 0
                                            if price["profitMargin"] == None:
                                                price["profitMargin"] = 0
                                            if price["posterDiscountRate"] == None:
                                                price["posterDiscountRate"] = 0
                                            if price["spoComissionType"] == 1:
                                                price["salePrice"] = price["perPersonPrice"] * \
                                                    price["factor"]
                                                price["salePrice"] -= (
                                                    price["salePrice"]*price["ebRate"]/100)
                                                price["salePrice"] -= (
                                                    price["salePrice"]*price["spoRate"]/100)
                                                price["salePrice"] += (
                                                    price["salePrice"]*price["profitMargin"]/100)
                                                price["posterPrice"] = price["salePrice"] + (
                                                    price["salePrice"]*price["posterDiscountRate"]/100)
                                            elif price["spoComissionType"] == 2:
                                                totalDiscountRate = price["ebRate"] + \
                                                    price["spoRate"]
                                                price["salePrice"] = price["perPersonPrice"] * \
                                                    price["factor"]
                                                price["salePrice"] -= (
                                                    price["salePrice"]*totalDiscountRate/100)
                                                price["salePrice"] += (
                                                    price["salePrice"]*price["profitMargin"]/100)
                                                price["posterPrice"] = price["salePrice"] + (
                                                    price["salePrice"]*price["posterDiscountRate"]/100)
                                        elif price["priceCalcType"] == 2:
                                            price["posterPrice"] = price["perPersonPrice"] * \
                                                price["factor"]
                                            price["salePrice"] = price["posterPrice"] - (
                                                price["posterPrice"]*price["posterDiscountRate"]/100)

        # Remove same dates from priceDictList
        # Because while calculation action Price is valid
        for actionDict in actionDictList:
            for priceDict in priceDictList:
                if actionDict["otelId"] == priceDict["otelId"]:
                    if actionDict["roomTypeId"] == priceDict["roomTypeId"]:
                        if actionDict["pensionTypeId"] == priceDict["pensionTypeId"]:
                            if actionDict["stayDate"] == priceDict["stayDate"]:
                                if priceDict in priceDictList:
                                    priceDictList.remove(priceDict)

        # concatenate actionDictList and priceDictList for calculation
        calculationList = actionDictList + priceDictList

        # get responseList structure before start to price calculation
        responseList = ReservationSearchFunctions.createResponseList(
            self, filteredQuotaList=filteredQuotaList, calculationList=calculationList)

        # Let's calculate prices for each response data
        priceInfo = {}
        for eachResponse in responseList:
            for calculation in calculationList:
                if eachResponse["otelId"] == calculation["otelId"]:
                    if eachResponse["roomTypeId"] == calculation["roomTypeId"]:
                        if eachResponse["conceptId"] == calculation["pensionTypeId"]:
                            eachResponse["salePrice"] += calculation["salePrice"]
                            eachResponse["posterPrice"] += calculation["posterPrice"]
                            priceInfo = {
                                str(calculation["stayDate"]): calculation["salePrice"]
                            }
                            eachResponse["priceList"].append(priceInfo)
            eachResponse["priceList"] = sorted(
                eachResponse["priceList"], key=lambda d: list(d.keys()))

        filteredResponseList = list(
            filter(lambda eachResponse: eachResponse["salePrice"] != 0, responseList))
        sortedResponseList = list(unique_everseen(
            sorted(filteredResponseList, key=lambda k: k["salePrice"])))
        grouppedResponseList = defaultdict(list)
        for eachSortedResponse in sortedResponseList:
            grouppedResponseList[eachSortedResponse["otelId"]].append(
                eachSortedResponse)

        responseData = {
            "count": len(sortedResponseList),
            "otelList": grouppedResponseList,
        }
        return JsonResponse(responseData)


class PriceCostInfo(APIView):

    """This api requires otelId in payload and returns roomType, pensionType, price and action infos"""

    def post(self, request, *args, **kwargs):
        otelId = request.data["otelId"]

        responseData = {}
        otelName = Otel.objects.get(id=otelId).name
        otelPriceStatus = Otel.objects.get(id=otelId).priceStatus
        roomTypes = list(RoomType.objects.filter(
            otel__id=otelId, isActive=True, isStatusActive=True).values("id", "name"))
        responseData["otelId"] = otelId
        responseData["otelName"] = otelName
        responseData["otelPriceStatus"] = otelPriceStatus
        responseData["roomTypes"] = roomTypes
        for eachRoomType in roomTypes:
            ebActions = list(MainAction.objects.filter(
                roomType__id=eachRoomType["id"], actionType=2, isActive=True, isStatusActive=True).values("id", "minimumStay", "maximumStay", "saleStartDate", "saleEndDate", "validDays", "excludeDates", "base", "pensionType__id", "pensionType__name", "accomodationStartDate", "accomodationEndDate", "actionType", "excludeDates", "validDays", "discount", "comissionType"))

            spoActions = list(MainAction.objects.filter(
                roomType__id=eachRoomType["id"], actionType=6, isActive=True, isStatusActive=True).values("id", "minimumStay", "maximumStay", "saleStartDate", "saleEndDate",  "validDays", "excludeDates", "base", "pensionType__id", "pensionType__name", "accomodationStartDate", "accomodationEndDate", "actionType", "excludeDates", "validDays", "discount", "comissionType"))

            priceDetails = list(PriceDetails.objects.filter(
                accomodation__roomType__id=eachRoomType["id"],  accomodation__isActive=True, accomodation__isStatusActive=True, priceTemplate__isActive=True, priceTemplate__isStatusActive=True, isActive=True, isStatusActive=True).values("id", "priceTemplate__id", "priceTemplate__salesChannel", "priceTemplate__minDays", "priceTemplate__maxDays", "accomodation__minimumDays", "accomodation__maximumDays", "accomodation__roomType__id", "accomodation__base", "accomodation__salesStartDate", "accomodation__salesFinishDate", "accomodation__startDate", "accomodation__finishDate", "accomodation__priceCalcType", "accomodation__comissionRate", "accomodation__concept__id", "accomodation__concept__name", "accomodation__excludeDates", "day1PerPersonPrice", "day2PerPersonPrice", "day3PerPersonPrice", "day4PerPersonPrice", "day5PerPersonPrice", "day6PerPersonPrice", "day7PerPersonPrice"))

            allData = {}
            for eachPriceDetail in priceDetails:
                priceDetailDelta = eachPriceDetail["accomodation__finishDate"] - \
                    eachPriceDetail["accomodation__startDate"]
                for i in range(priceDetailDelta.days + 1):
                    eachDay = eachPriceDetail["accomodation__startDate"] + \
                        timedelta(days=i)
                    if eachPriceDetail["accomodation__concept__id"] not in allData.keys():
                        allData[eachPriceDetail["accomodation__concept__id"]] = {}
                    if eachPriceDetail["priceTemplate__id"] not in allData[eachPriceDetail["accomodation__concept__id"]].keys():
                        allData[eachPriceDetail["accomodation__concept__id"]
                                ][eachPriceDetail["priceTemplate__id"]] = {}
                    if eachDay not in allData[eachPriceDetail["accomodation__concept__id"]][eachPriceDetail["priceTemplate__id"]].keys():
                        allData[eachPriceDetail["accomodation__concept__id"]
                                ][eachPriceDetail["priceTemplate__id"]][eachDay] = {}
                    if eachDay not in eachPriceDetail["accomodation__excludeDates"]:
                        allData[eachPriceDetail["accomodation__concept__id"]
                                ][eachPriceDetail["priceTemplate__id"]][eachDay]['normal'] = eachPriceDetail

                for eachEbAction in ebActions:
                    ebDelta = eachEbAction["accomodationEndDate"] - \
                        eachEbAction["accomodationStartDate"]
                    for i in range(ebDelta.days + 1):
                        eachDay = eachEbAction["accomodationStartDate"] + \
                            timedelta(days=i)
                        if eachEbAction["pensionType__id"] in allData.keys():
                            if eachPriceDetail["priceTemplate__id"] in allData[eachEbAction["pensionType__id"]].keys():
                                if eachDay in allData[eachEbAction["pensionType__id"]][eachPriceDetail["priceTemplate__id"]].keys():
                                    if eachDay not in eachEbAction["excludeDates"]:
                                        if datetime.strptime(str(eachDay), '%Y-%m-%d').weekday() + 1 in eachEbAction["validDays"]:
                                            allData[eachEbAction["pensionType__id"]
                                                    ][eachPriceDetail["priceTemplate__id"]][eachDay]['ebAction'] = eachEbAction

                for eachSpoAction in spoActions:
                    spoDelta = eachSpoAction["accomodationEndDate"] - \
                        eachSpoAction["accomodationStartDate"]
                    for i in range(spoDelta.days + 1):
                        eachDay = eachSpoAction["accomodationStartDate"] + \
                            timedelta(days=i)
                        if eachSpoAction["pensionType__id"] in allData.keys():
                            if eachPriceDetail["priceTemplate__id"] in allData[eachSpoAction["pensionType__id"]].keys():
                                if eachDay in allData[eachSpoAction["pensionType__id"]][eachPriceDetail["priceTemplate__id"]].keys():
                                    if eachDay not in eachSpoAction["excludeDates"]:
                                        if datetime.strptime(str(eachDay), '%Y-%m-%d').weekday() + 1 in eachSpoAction["validDays"]:
                                            allData[eachSpoAction["pensionType__id"]
                                                    ][eachPriceDetail["priceTemplate__id"]][eachDay]['spoAction'] = eachSpoAction
            priceDetailList = []
            for eachPansionType in allData:
                for eachPriceTemplateId in allData[eachPansionType]:
                    tempList = []
                    tempId = ""
                    for eachDay in allData[eachPansionType][eachPriceTemplateId]:
                        dataOfDay = allData[eachPansionType][eachPriceTemplateId][eachDay]
                        idOfDay = PriceCostInfoFunctions.calculateId(
                            self, dictionary=dataOfDay)
                        if len(tempList) == 0:
                            tempId = idOfDay
                            tempList.append({eachDay: dataOfDay})
                        else:
                            if idOfDay == tempId:
                                tempList.append({eachDay: dataOfDay})
                            else:
                                priceDetailList.append(
                                    PriceCostInfoFunctions.createPriceDetailListData(self, priceList=tempList))
                                tempList.clear()
                                tempList.append({eachDay: dataOfDay})
                                tempId = idOfDay
                    if len(tempList) != 0:
                        priceDetailList.append(
                            PriceCostInfoFunctions.createPriceDetailListData(self, priceList=tempList))
                    tempList.clear()
                    tempId = ""
            filteredPriceDetailList = list(
                filter(lambda eachPriceDetail: eachPriceDetail != {}, priceDetailList))
            eachRoomType["priceDetails"] = filteredPriceDetailList
            actionPriceDetails = list(ActionPriceDetail.objects.filter(action__roomType__id=eachRoomType["id"], action__isActive=True, action__isStatusActive=True, priceTemplate__isActive=True, priceTemplate__isStatusActive=True, isActive=True, isStatusActive=True).values("id", "priceTemplate__id", "priceTemplate__salesChannel", "priceTemplate__minDays", "priceTemplate__maxDays", "action__minimumStay", "action__maximumStay", "action__excludeDates", "action__base", "action__pensionType__id", "action__pensionType__name", "action__saleStartDate", "action__saleEndDate",
                                                                                                                                                                                                                                                                                 "action__accomodationStartDate", "action__accomodationEndDate", "action__actionType", "action__priceCalculationType", "action__discount", "day1PerPersonPrice", "day2PerPersonPrice", "day3PerPersonPrice", "day4PerPersonPrice", "day5PerPersonPrice", "day6PerPersonPrice", "day7PerPersonPrice"))

            allActionData = {}
            for eachActionPriceDetail in actionPriceDetails:
                actionPriceDetailDelta = eachActionPriceDetail["action__accomodationEndDate"] - \
                    eachActionPriceDetail["action__accomodationStartDate"]
                for i in range(actionPriceDetailDelta.days + 1):
                    eachDay = eachActionPriceDetail["action__accomodationStartDate"] + \
                        timedelta(days=i)
                    if eachActionPriceDetail["action__pensionType__id"] not in allActionData.keys():
                        allActionData[eachActionPriceDetail["action__pensionType__id"]] = {
                        }
                    if eachActionPriceDetail["priceTemplate__id"] not in allActionData[eachActionPriceDetail["action__pensionType__id"]].keys():
                        allActionData[eachActionPriceDetail["action__pensionType__id"]
                                      ][eachActionPriceDetail["priceTemplate__id"]] = {}
                    if eachDay not in allActionData[eachActionPriceDetail["action__pensionType__id"]][eachActionPriceDetail["priceTemplate__id"]].keys():
                        allActionData[eachActionPriceDetail["action__pensionType__id"]
                                      ][eachActionPriceDetail["priceTemplate__id"]][eachDay] = {}
                    if eachDay not in eachActionPriceDetail["action__excludeDates"]:
                        allActionData[eachActionPriceDetail["action__pensionType__id"]
                                      ][eachActionPriceDetail["priceTemplate__id"]][eachDay]['pAction'] = eachActionPriceDetail

                for eachEbAction in ebActions:
                    ebDelta = eachEbAction["accomodationEndDate"] - \
                        eachEbAction["accomodationStartDate"]
                    for i in range(ebDelta.days + 1):
                        eachDay = eachEbAction["accomodationStartDate"] + \
                            timedelta(days=i)
                        if eachEbAction["pensionType__id"] in allActionData.keys():
                            if eachActionPriceDetail["priceTemplate__id"] in allActionData[eachEbAction["pensionType__id"]].keys():
                                if eachDay in allActionData[eachEbAction["pensionType__id"]][eachActionPriceDetail["priceTemplate__id"]].keys():
                                    if eachDay not in eachEbAction["excludeDates"]:
                                        if datetime.strptime(str(eachDay), '%Y-%m-%d').weekday() + 1 in eachEbAction["validDays"]:
                                            allActionData[eachEbAction["pensionType__id"]
                                                          ][eachActionPriceDetail["priceTemplate__id"]][eachDay]['ebAction'] = eachEbAction

                for eachSpoAction in spoActions:
                    spoDelta = eachSpoAction["accomodationEndDate"] - \
                        eachSpoAction["accomodationStartDate"]
                    for i in range(spoDelta.days + 1):
                        eachDay = eachSpoAction["accomodationStartDate"] + \
                            timedelta(days=i)
                        if eachSpoAction["pensionType__id"] in allActionData.keys():
                            if eachActionPriceDetail["priceTemplate__id"] in allActionData[eachSpoAction["pensionType__id"]].keys():
                                if eachDay in allActionData[eachSpoAction["pensionType__id"]][eachActionPriceDetail["priceTemplate__id"]].keys():
                                    if eachDay not in eachSpoAction["excludeDates"]:
                                        if datetime.strptime(str(eachDay), '%Y-%m-%d').weekday() + 1 in eachSpoAction["validDays"]:
                                            allActionData[eachSpoAction["pensionType__id"]
                                                          ][eachActionPriceDetail["priceTemplate__id"]][eachDay]['spoAction'] = eachSpoAction

            actionPriceDetailList = []
            for eachPansionType in allActionData:
                for eachPriceTemplateId in allActionData[eachPansionType]:
                    tempList = []
                    tempId = ""
                    for eachDay in allActionData[eachPansionType][eachPriceTemplateId]:
                        dataOfDay = allActionData[eachPansionType][eachPriceTemplateId][eachDay]
                        idOfDay = PriceCostInfoFunctions.calculateActionId(
                            self, dictionary=dataOfDay)
                        if len(tempList) == 0:
                            tempId = idOfDay
                            tempList.append({eachDay: dataOfDay})
                        else:
                            if idOfDay == tempId:
                                tempList.append({eachDay: dataOfDay})
                            else:
                                actionPriceDetailList.append(
                                    PriceCostInfoFunctions.createActionPriceDetailListData(self, priceList=tempList))
                                tempList.clear()
                                tempList.append({eachDay: dataOfDay})
                                tempId = idOfDay
                    if len(tempList) != 0:
                        actionPriceDetailList.append(
                            PriceCostInfoFunctions.createActionPriceDetailListData(self, priceList=tempList))
                    tempList.clear()
                    tempId = ""
            filteredActionPriceDetail = list(
                filter(lambda eachActionPriceDetail: eachActionPriceDetail != {}, actionPriceDetailList))
            eachRoomType["actionPriceDetails"] = filteredActionPriceDetail

        return JsonResponse(responseData)
