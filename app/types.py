import enum
import functools


class Type(enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    LIST = "LIST"
    BOOLEAN = "BOOLEAN"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    HIDDEN = "HIDDEN"
    LIKERT = "LIKERT"
    ONE_TO_SEVEN = "ONE_TO_SEVEN"
    ONE_TO_FIVE = "ONE_TO_FIVE"
    ONE_TO_THREE = "ONE_TO_THREE"

    def serialise(self):
        return self.value

    def export():
        return {entry.name: entry.value for entry in Type}


@functools.total_ordering
class AccessLevel(enum.Enum):
    NONE = 0
    CODE = 1
    EXPORT = 2
    ADMIN = 3

    def grants(self, other):
        return other.value <= self.value

    def __gt__(self, other):
        return other.value < self.value
