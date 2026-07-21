class FactoryMESError(Exception):
    pass


class ValidationError(FactoryMESError):
    pass


class NotFoundError(FactoryMESError):
    pass


class DuplicateError(FactoryMESError):
    pass


class DatabaseError(FactoryMESError):
    pass