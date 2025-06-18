from multiprocessing import Manager

# 你可以在启动时创建一个共享的缓存
manager = Manager()
# 返回一个缓存字典
shared_cache = manager.dict()
