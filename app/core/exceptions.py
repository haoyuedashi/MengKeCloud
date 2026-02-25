class AppException(Exception):
    def __init__(
        self,
        message: str,
        business_code: int = 400,
        status_code: int = 400,
        data: object | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.business_code = business_code
        self.status_code = status_code
        self.data = data
