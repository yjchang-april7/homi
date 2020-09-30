class HomiError(BaseException):
    pass


class ServerConfigError(HomiError):
    pass
class ServerSSLConfigError(ServerConfigError):
    pass

class ServiceError(HomiError):
    pass