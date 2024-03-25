class Middleware:
    def __init__(self, middlewares: list | None = None):
        self.middlewares = []
        self.middlewares = middlewares or []

    def add_middleware(self, middleware) -> None:
        self.middlewares.append(middleware)

    def handle(self, event, bot):
        raise NotImplementedError
