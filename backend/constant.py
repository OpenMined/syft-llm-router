from enum import Enum


class PricingChargeType(str, Enum):
    PER_REQUEST = "per_request"


class RouterServiceType(str, Enum):
    CHAT = "chat"
    SEARCH = "search"

    @classmethod
    def all_types(cls):
        return [service.value for service in cls]


class RouterType(str, Enum):
    DEFAULT = "default"
    CUSTOM = "custom"
