from accomodations.models import PensionType, RoomType
from otels.models import Otel, OtelImages


class PriceCostInfoFunctions():
    def calculateId(self, dictionary):
        id = ""
        if "normal" in dictionary.keys():
            id += "n"+str(dictionary["normal"]["id"])
        if "ebAction" in dictionary.keys():
            id += "e"+str(dictionary["ebAction"]["id"])
        if "spoAction" in dictionary.keys():
            id += "s"+str(dictionary["spoAction"]["id"])
        return id

    def calculateActionId(self, dictionary):
        id = ""
        if "pAction" in dictionary.keys():
            id += "p"+str(dictionary["pAction"]["id"])
        if "ebAction" in dictionary.keys():
            id += "e"+str(dictionary["ebAction"]["id"])
        if "spoAction" in dictionary.keys():
            id += "s"+str(dictionary["spoAction"]["id"])
        return id

    def createPriceDetailListData(self, priceList):
        from accomodations.models import PriceTemplate
        startDate = list(priceList[0].keys())[0]
        endDate = list(priceList[-1].keys())[0]
        priceDetailDict = {}
        if "normal" in priceList[0][startDate].keys():
            normalPrice = priceList[0][startDate]["normal"]
            salesChannel = list(PriceTemplate.objects.filter(
                id=normalPrice["priceTemplate__id"]).values_list("salesChannel__id", flat=True))
            priceDetailDict = {
                "priceId": normalPrice["id"],
                "startDate": startDate,
                "endDate": endDate,
                "minDays":  normalPrice["accomodation__minimumDays"],
                "maxDays":  normalPrice["accomodation__maximumDays"],
                "priceMinDays": normalPrice["priceTemplate__minDays"],
                "priceMaxDays": normalPrice["priceTemplate__maxDays"],
                "priceTemplateId": normalPrice["priceTemplate__id"],
                "salesChannel": salesChannel,
                "base": normalPrice["accomodation__base"],
                "saleStartDate": normalPrice["accomodation__salesStartDate"],
                "saleEndDate": normalPrice["accomodation__salesFinishDate"],
                "priceCalcType": normalPrice["accomodation__priceCalcType"],
                "comissionRate": normalPrice["accomodation__comissionRate"],
                "conceptId": normalPrice["accomodation__concept__id"],
                "conceptName": normalPrice["accomodation__concept__name"],
                "day1PerPersonPrice": normalPrice["day1PerPersonPrice"],
                "day2PerPersonPrice": normalPrice["day2PerPersonPrice"],
                "day3PerPersonPrice": normalPrice["day3PerPersonPrice"],
                "day4PerPersonPrice": normalPrice["day4PerPersonPrice"],
                "day5PerPersonPrice": normalPrice["day5PerPersonPrice"],
                "day6PerPersonPrice": normalPrice["day6PerPersonPrice"],
                "day7PerPersonPrice": normalPrice["day7PerPersonPrice"],
                "ebId": None,
                "ebComissionType": None,
                "ebRate": None,
                "ebBase": None,
                "ebValidDays": None,
                "ebExcludeDates": None,
                "spoId": None,
                "spoComissionType": None,
                "spoRate": None,
                "spoBase": None,
                "spoValidDays": None,
                "spoExcludeDates": None
            }
            if "ebAction" in priceList[0][startDate]:
                if priceList[0][startDate]["ebAction"]["pensionType__id"] == priceDetailDict["conceptId"]:
                    priceDetailDict["ebComissionType"] = priceList[0][startDate]["ebAction"]["comissionType"]
                    priceDetailDict["ebRate"] = priceList[0][startDate]["ebAction"]["discount"]
                    priceDetailDict["ebBase"] = priceList[0][startDate]["ebAction"]["base"]
                    priceDetailDict["ebValidDays"] = priceList[0][startDate]["ebAction"]["validDays"]
                    priceDetailDict["ebExcludeDates"] = priceList[0][startDate]["ebAction"]["excludeDates"]
                    priceDetailDict["ebId"] = priceList[0][startDate]["ebAction"]["id"]

            if "spoAction" in priceList[0][startDate]:
                if priceList[0][startDate]["spoAction"]["pensionType__id"] == priceDetailDict["conceptId"]:
                    priceDetailDict["spoComissionType"] = priceList[0][startDate]["spoAction"]["comissionType"]
                    priceDetailDict["spoRate"] = priceList[0][startDate]["spoAction"]["discount"]
                    priceDetailDict["spoBase"] = priceList[0][startDate]["spoAction"]["base"]
                    priceDetailDict["spoValidDays"] = priceList[0][startDate]["spoAction"]["validDays"]
                    priceDetailDict["spoExcludeDates"] = priceList[0][startDate]["spoAction"]["excludeDates"]
                    priceDetailDict["spoId"] = priceList[0][startDate]["spoAction"]["id"]

            unitPrice = 100
            if (priceDetailDict["comissionRate"] != None) and (priceDetailDict["priceCalcType"] == 2):
                comissionPrice = unitPrice * \
                    priceDetailDict["comissionRate"]/100
            else:
                comissionPrice = 0
            finalPrice = unitPrice - comissionPrice
            if (priceDetailDict["ebRate"] != None):
                if priceDetailDict["ebComissionType"] == 1:
                    finalPrice *= (100-priceDetailDict["ebRate"])/100
                elif priceDetailDict["ebComissionType"] == 2:
                    finalPrice -= (unitPrice*priceDetailDict["ebRate"]/100)
            if (priceDetailDict["spoRate"] != None):
                if priceDetailDict["spoComissionType"] == 1:
                    finalPrice *= (100-priceDetailDict["spoRate"])/100
                elif priceDetailDict["spoComissionType"] == 2:
                    finalPrice -= (unitPrice*priceDetailDict["spoRate"]/100)

            priceDetailDict["day1HdsPrice"] = priceDetailDict["day1PerPersonPrice"] * \
                ((100-finalPrice)/100)
            priceDetailDict["day2HdsPrice"] = priceDetailDict["day2PerPersonPrice"] * \
                ((100-finalPrice)/100)
            priceDetailDict["day3HdsPrice"] = priceDetailDict["day3PerPersonPrice"] * \
                ((100-finalPrice)/100)
            priceDetailDict["day4HdsPrice"] = priceDetailDict["day4PerPersonPrice"] * \
                ((100-finalPrice)/100)
            priceDetailDict["day5HdsPrice"] = priceDetailDict["day5PerPersonPrice"] * \
                ((100-finalPrice)/100)
            priceDetailDict["day6HdsPrice"] = priceDetailDict["day6PerPersonPrice"] * \
                ((100-finalPrice)/100)
            priceDetailDict["day7HdsPrice"] = priceDetailDict["day7PerPersonPrice"] * \
                ((100-finalPrice)/100)
            priceDetailDict["day1OtelPrice"] = priceDetailDict["day1PerPersonPrice"] - \
                priceDetailDict["day1HdsPrice"]
            priceDetailDict["day2OtelPrice"] = priceDetailDict["day2PerPersonPrice"] - \
                priceDetailDict["day2HdsPrice"]
            priceDetailDict["day3OtelPrice"] = priceDetailDict["day3PerPersonPrice"] - \
                priceDetailDict["day3HdsPrice"]
            priceDetailDict["day4OtelPrice"] = priceDetailDict["day4PerPersonPrice"] - \
                priceDetailDict["day4HdsPrice"]
            priceDetailDict["day5OtelPrice"] = priceDetailDict["day5PerPersonPrice"] - \
                priceDetailDict["day5HdsPrice"]
            priceDetailDict["day6OtelPrice"] = priceDetailDict["day6PerPersonPrice"] - \
                priceDetailDict["day6HdsPrice"]
            priceDetailDict["day7OtelPrice"] = priceDetailDict["day7PerPersonPrice"] - \
                priceDetailDict["day7HdsPrice"]

        return priceDetailDict

    def createActionPriceDetailListData(self, priceList):
        from actions.models import ActionPriceTemplate
        startDate = list(priceList[0].keys())[0]
        endDate = list(priceList[-1].keys())[0]
        actionPriceDetailDict = {}
        if "pAction" in priceList[0][startDate].keys():
            actionPrice = priceList[0][startDate]["pAction"]
            salesChannel = list(ActionPriceTemplate.objects.filter(
                id=actionPrice["priceTemplate__id"]).values_list("salesChannel__id", flat=True))
            actionPriceDetailDict = {
                "actionPriceId": actionPrice["id"],
                "startDate": startDate,
                "endDate": endDate,
                "minDays":  actionPrice["action__minimumStay"],
                "maxDays":  actionPrice["action__maximumStay"],
                "priceMinDays": actionPrice["priceTemplate__minDays"],
                "priceMaxDays": actionPrice["priceTemplate__maxDays"],
                "priceTemplateId": actionPrice["priceTemplate__id"],
                "salesChannel": salesChannel,
                "base": actionPrice["action__base"],
                "saleStartDate": actionPrice["action__saleStartDate"],
                "saleEndDate": actionPrice["action__saleEndDate"],
                "priceCalcType": actionPrice["action__priceCalculationType"],
                "comissionRate": actionPrice["action__discount"],
                "conceptId": actionPrice["action__pensionType__id"],
                "conceptName": actionPrice["action__pensionType__name"],
                "day1PerPersonPrice": actionPrice["day1PerPersonPrice"],
                "day2PerPersonPrice": actionPrice["day2PerPersonPrice"],
                "day3PerPersonPrice": actionPrice["day3PerPersonPrice"],
                "day4PerPersonPrice": actionPrice["day4PerPersonPrice"],
                "day5PerPersonPrice": actionPrice["day5PerPersonPrice"],
                "day6PerPersonPrice": actionPrice["day6PerPersonPrice"],
                "day7PerPersonPrice": actionPrice["day7PerPersonPrice"],
                "ebId": None,
                "ebComissionType": None,
                "ebRate": None,
                "ebBase": None,
                "ebValidDays": None,
                "ebExcludeDates": None,
                "spoId": None,
                "spoComissionType": None,
                "spoRate": None,
                "spoBase": None,
                "spoValidDays": None,
                "spoValidDays": None,
                "spoExcludeDates": None
            }
            if "ebAction" in priceList[0][startDate]:
                if priceList[0][startDate]["ebAction"]["pensionType__id"] == actionPriceDetailDict["conceptId"]:
                    actionPriceDetailDict["ebComissionType"] = priceList[0][startDate]["ebAction"]["comissionType"]
                    actionPriceDetailDict["ebRate"] = priceList[0][startDate]["ebAction"]["discount"]
                    actionPriceDetailDict["ebBase"] = priceList[0][startDate]["ebAction"]["base"]
                    actionPriceDetailDict["ebValidDays"] = priceList[0][startDate]["ebAction"]["validDays"]
                    actionPriceDetailDict["ebExcludeDates"] = priceList[0][startDate]["ebAction"]["excludeDates"]
                    actionPriceDetailDict["ebId"] = priceList[0][startDate]["ebAction"]["id"]

            if "spoAction" in priceList[0][startDate]:
                if priceList[0][startDate]["spoAction"]["pensionType__id"] == actionPriceDetailDict["conceptId"]:
                    actionPriceDetailDict["spoComissionType"] = priceList[0][startDate]["spoAction"]["comissionType"]
                    actionPriceDetailDict["spoRate"] = priceList[0][startDate]["spoAction"]["discount"]
                    actionPriceDetailDict["spoBase"] = priceList[0][startDate]["spoAction"]["base"]
                    actionPriceDetailDict["spoValidDays"] = priceList[0][startDate]["spoAction"]["validDays"]
                    actionPriceDetailDict["spoExcludeDates"] = priceList[0][startDate]["spoAction"]["excludeDates"]
                    actionPriceDetailDict["spoId"] = priceList[0][startDate]["spoAction"]["id"]

            unitPrice = 100
            if (actionPriceDetailDict["comissionRate"] != None) and (actionPriceDetailDict["priceCalcType"] == 2):
                comissionPrice = unitPrice * \
                    actionPriceDetailDict["comissionRate"]/100
            else:
                comissionPrice = 0
            finalPrice = unitPrice - comissionPrice
            if (actionPriceDetailDict["ebRate"] != None):
                if actionPriceDetailDict["ebComissionType"] == 1:
                    finalPrice *= (100-actionPriceDetailDict["ebRate"])/100
                elif actionPriceDetailDict["ebComissionType"] == 2:
                    finalPrice -= (unitPrice *
                                   actionPriceDetailDict["ebRate"]/100)
            if (actionPriceDetailDict["spoRate"] != None):
                if actionPriceDetailDict["spoComissionType"] == 1:
                    finalPrice *= (100-actionPriceDetailDict["spoRate"])/100
                elif actionPriceDetailDict["spoComissionType"] == 2:
                    finalPrice -= (unitPrice *
                                   actionPriceDetailDict["spoRate"]/100)

            actionPriceDetailDict["day1HdsPrice"] = actionPriceDetailDict["day1PerPersonPrice"] * \
                ((100-finalPrice)/100)
            actionPriceDetailDict["day2HdsPrice"] = actionPriceDetailDict["day2PerPersonPrice"] * \
                ((100-finalPrice)/100)
            actionPriceDetailDict["day3HdsPrice"] = actionPriceDetailDict["day3PerPersonPrice"] * \
                ((100-finalPrice)/100)
            actionPriceDetailDict["day4HdsPrice"] = actionPriceDetailDict["day4PerPersonPrice"] * \
                ((100-finalPrice)/100)
            actionPriceDetailDict["day5HdsPrice"] = actionPriceDetailDict["day5PerPersonPrice"] * \
                ((100-finalPrice)/100)
            actionPriceDetailDict["day6HdsPrice"] = actionPriceDetailDict["day6PerPersonPrice"] * \
                ((100-finalPrice)/100)
            actionPriceDetailDict["day7HdsPrice"] = actionPriceDetailDict["day7PerPersonPrice"] * \
                ((100-finalPrice)/100)
            actionPriceDetailDict["day1OtelPrice"] = actionPriceDetailDict["day1PerPersonPrice"] - \
                actionPriceDetailDict["day1HdsPrice"]
            actionPriceDetailDict["day2OtelPrice"] = actionPriceDetailDict["day2PerPersonPrice"] - \
                actionPriceDetailDict["day2HdsPrice"]
            actionPriceDetailDict["day3OtelPrice"] = actionPriceDetailDict["day3PerPersonPrice"] - \
                actionPriceDetailDict["day3HdsPrice"]
            actionPriceDetailDict["day4OtelPrice"] = actionPriceDetailDict["day4PerPersonPrice"] - \
                actionPriceDetailDict["day4HdsPrice"]
            actionPriceDetailDict["day5OtelPrice"] = actionPriceDetailDict["day5PerPersonPrice"] - \
                actionPriceDetailDict["day5HdsPrice"]
            actionPriceDetailDict["day6OtelPrice"] = actionPriceDetailDict["day6PerPersonPrice"] - \
                actionPriceDetailDict["day6HdsPrice"]
            actionPriceDetailDict["day7OtelPrice"] = actionPriceDetailDict["day7PerPersonPrice"] - \
                actionPriceDetailDict["day7HdsPrice"]

        return actionPriceDetailDict


class ReservationSearchFunctions():
    """
    This class contains reservationSearch api functions
    """

    def createResponseList(self, filteredQuotaList, calculationList):
        resultResponseList = []
        for filteredQuota in filteredQuotaList:
            filteredQuota["roomTypeFeature"] = list(RoomType.objects.filter(
                id=filteredQuota["roomType__id"], isActive=True, isStatusActive=True).values("feature__id", "feature__name"))
            filteredQuota["roomTypeSize"] = RoomType.objects.filter(
                id=filteredQuota["roomType__id"], isActive=True, isStatusActive=True).values_list("roomSize", flat=True).first()
            filteredQuota["roomTypeGuestCount"] = RoomType.objects.filter(
                id=filteredQuota["roomType__id"], isActive=True, isStatusActive=True).values_list("guestCount", flat=True).first()
            filteredQuota["otelCategories"] = list(Otel.objects.filter(
                id=filteredQuota["otel__id"], isActive=True, isStatusActive=True).values("category__id", "category__name"))
            for calculationPrice in calculationList:
                if filteredQuota["roomType__id"] == calculationPrice["roomTypeId"]:
                    filteredQuota["conceptId"] = PensionType.objects.get(
                        id=calculationPrice["pensionTypeId"]).id
                    filteredQuota["conceptName"] = PensionType.objects.get(
                        id=calculationPrice["pensionTypeId"]).name
                    eachResponse = {
                        "quotaId": filteredQuota["id"],
                        "otelId": filteredQuota["otel__id"],
                        "otelName": filteredQuota["otel__name"],
                        "otelRegion": filteredQuota["otel__region__name"],
                        "otelSubRegion": filteredQuota["otel__subRegion__name"],
                        "otelLocation": filteredQuota["otel__location__name"],
                        "roomTypeId": filteredQuota["roomType__id"],
                        "roomTypeName": filteredQuota["roomType__name"],
                        "quotaDate": filteredQuota["quotaDate"],
                        "quota": filteredQuota["quota"],
                        "status": filteredQuota["status"],
                        "conceptId": filteredQuota["conceptId"],
                        "conceptName": filteredQuota["conceptName"],
                        "roomTypeFeature": filteredQuota["roomTypeFeature"],
                        "roomTypeSize": filteredQuota["roomTypeSize"],
                        "roomTypeGuestCount": filteredQuota["roomTypeGuestCount"],
                        "otelCategories": filteredQuota["otelCategories"],
                        "salePrice": 0,
                        "posterPrice": 0,
                        "priceList": []
                    }
                    resultResponseList.append(eachResponse)
        return resultResponseList
