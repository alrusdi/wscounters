class BaseStorage:
    async def create(self):
        raise NotImplementedError()

    async def save(self, data):
        raise NotImplementedError()
