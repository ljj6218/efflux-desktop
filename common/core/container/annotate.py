
def component(cls):
    setattr(cls, '__component__', True)  # 标记这个类是 injectable
    return cls