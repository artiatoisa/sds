class SdsHttpException(Exception):
    pass


class SdsHttpResultCodeException(SdsHttpException):
    pass


class SdsAuthException(Exception):
    pass


class SdsAppCodeException(SdsAuthException):
    pass


class SdsAppTokenException(SdsAuthException):
    pass


class SdsSlidUserTokenException(SdsAuthException):
    pass


class SdsSlnetTokenException(SdsAuthException):
    pass


class SdsDataException(Exception):
    pass


class SdsUserDataException(SdsDataException):
    pass


class SdsEventsException(SdsDataException):
    pass


class SdsOBDException(SdsDataException):
    pass
