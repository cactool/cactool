import enum
class Type(enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    LIST = "LIST"
    BOOLEAN = "BOOLEAN"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    
    def serialise(self):
        return self.value
    
    def export():
        return {entry.name: entry.value for entry in Type }

class AccessType(enum.Enum):
    NONE = 0
    CODE = 1
    EXPORT = 2
    ADMIN = 3