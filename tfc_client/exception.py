class TFCClientException(Exception):
    pass


class APIException(TFCClientException):
    pass


class TFCObjectException(TFCClientException):
    pass


class UnmanagedObjectTypeException(TFCObjectException):
    pass
