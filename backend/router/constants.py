from enum import Enum

PUBLIC_ROUTER_DIR_NAME = "public"
ROUTER_DIR_NAME = "routers"


class DelegateControlType(str, Enum):
    """Types of controls delegates can perform."""

    UPDATE_PRICING = "update_pricing"

    @classmethod
    def all_types(cls):
        return [control.value for control in cls]


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
