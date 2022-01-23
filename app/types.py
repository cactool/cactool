import enum
class Type(enum.Enum):
    STRING = "string"
    NUMBER = "number"
    LIST = "list"
    BOOLEAN = "boolean"
    SOCIAL_MEDIA = "social_media"

class AccessType(enum.Enum):
    NONE = 0
    CODE = 1
    EXPORT = 2
    ADMIN = 3