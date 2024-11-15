import odin

from oscar.core.loading import get_class, get_model

ModelMapping = get_class("oscar_odin.mappings.model_mapper", "ModelMapping")
OscarBaseMapping = get_class("oscar_odin.mappings.common", "OscarBaseMapping")

# resources
PartnerResource = get_class("oscar_odin.resources.partner", "PartnerResource")
StockRecordResource = get_class("oscar_odin.resources.partner", "StockRecordResource")

Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")


class PartnerModelToResource(OscarBaseMapping):
    from_obj = Partner
    to_obj = PartnerResource


class PartnerToModel(OscarBaseMapping):
    from_obj = PartnerResource
    to_obj = Partner


class StockRecordModelToResource(OscarBaseMapping):
    from_obj = StockRecord
    to_obj = StockRecordResource

    @odin.map_field
    def partner(self, partner):
        return PartnerModelToResource.apply(partner)


class StockRecordToModel(OscarBaseMapping):
    from_obj = StockRecordResource
    to_obj = StockRecord

    @odin.map_field
    def partner(self, partner):
        return PartnerToModel.apply(partner)
