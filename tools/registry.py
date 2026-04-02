class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, func):
        self.tools[name] = func

    def call(self, name, **kwargs):
        if name not in self.tools:
            raise KeyError(f"Tool not found: {name}")
        return self.tools[name](**kwargs)
