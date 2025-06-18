import inspect
import os
import importlib.util
import importlib
import injector
from injector import Injector
import sys
from typing import Type, get_args
from common.core.logger import get_logger

logger = get_logger(__name__)

# 动态获取项目根目录路径
def get_project_root():
    """
    动态获取项目根目录
    1. 尝试从模块结构推断: 寻找包含 'adapter' 和 'application' 目录的文件夹
    2. 如果失败, 回退到当前工作目录
    """
    # 获取当前模块的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 向上查找，直到找到包含 adapter 和 application 目录的文件夹
    path = current_dir
    while True:
        # 检查是否存在 adapter 和 application 目录
        if os.path.isdir(os.path.join(path, 'adapter')) and os.path.isdir(os.path.join(path, 'application')):
            return path
        
        # 获取父目录
        parent = os.path.dirname(path)
        # 如果已经到达根目录，则使用当前工作目录作为后备
        if parent == path:
            logger.error(f"警告: 无法自动确定项目根目录, 使用当前工作目录: {os.getcwd()}")
            return os.getcwd()
        path = parent

PROJECT_ROOT = get_project_root()
logger.info(f"项目根目录: {PROJECT_ROOT}")

# 创建一个动态扫描和绑定服务的容器
class Container(injector.Module):

    def configure(self, binder):
        # 获取所有组件类
        component_classes = []
        # 仅扫描特定目录，避免扫描整个项目
        scan_for_components('adapter', component_classes)
        scan_for_components('application', component_classes)
        # 首先绑定所有组件类到它们自身
        for cls in component_classes:
            binder.bind(cls, to=cls, scope=injector.singleton)
        # 然后处理抽象类到实现类的绑定
        for cls in component_classes:
            # 获取该类实现的所有基类（包括抽象类）
            for base in cls.__bases__:
                if inspect.isabstract(base):
                    # 如果是抽象基类，绑定抽象基类到这个实现
                    logger.info(f"Binding abstract class {base.__name__} to implementation {cls.__name__}")
                    binder.bind(base, to=cls, scope=injector.singleton)
        # 处理集合类型注入（如 List[TaskHandler]）
        for cls in component_classes:
            # 检查是否有构造函数，获取参数类型
            if hasattr(cls, '__init__'):
                signature = inspect.signature(cls.__init__)
                for param in signature.parameters.values():
                    param_type = param.annotation
                    # 如果参数类型是 List[TaskHandler]
                    if hasattr(param_type, "__origin__") and param_type.__origin__ is list:
                        item_type = param_type.__args__[0]  # 获取 List 中的类型
                        task_handlers = []
                        # 收集所有 TaskHandler 实现类
                        for component_class in component_classes:
                            cc = extract_type(item_type)
                            if issubclass(component_class, cc):
                                task_handlers.append(component_class)
                        binder.multibind(param_type, to=task_handlers, scope=injector.singleton)

def extract_type(annotated_type):
    # 如果是 Type[SomeClass]，返回 SomeClass
    if hasattr(annotated_type, '__origin__') and annotated_type.__origin__ is type:
        return get_args(annotated_type)[0]
    return annotated_type

def convert_path_to_module(path) -> str:
    """将文件路径转换为模块路径"""
    rel_path = os.path.relpath(path, PROJECT_ROOT)
    # 将路径分隔符替换为点，并移除.py扩展名
    module_path = rel_path.replace('/', '.').replace('\\', '.').replace('.py', '')
    return str(module_path)

def scan_for_components(package_name, component_classes):
    """
    扫描指定包内的所有组件类
    """
    # 获取包的完整路径
    package_path = os.path.join(PROJECT_ROOT, package_name)
    # 确保目录存在
    if not os.path.isdir(package_path):
        logger.error(f"Directory not found: {package_path}")
        return
    # 初始化已处理的模块集合
    processed_modules = set()
    # 使用队列进行广度优先搜索
    dirs_to_scan = [package_path]
    while dirs_to_scan:
        current_dir = dirs_to_scan.pop(0)
        try:
            # 获取当前目录中的所有项目
            items = os.listdir(current_dir)
            # 处理所有 Python 文件和子目录
            for item in items:
                item_path = os.path.join(current_dir, item)
                # 如果是目录且不是隐藏目录，则添加到队列
                if os.path.isdir(item_path) and not item.startswith('.') and item != '__pycache__':
                    dirs_to_scan.append(item_path)
                    # 确保每个包目录都有 __init__.py
                    init_file = os.path.join(item_path, '__init__.py')
                    if not os.path.exists(init_file):
                        logger.error(f"Warning: Missing __init__.py in {item_path}")
                # 如果是 Python 文件且不是 __init__.py，尝试导入
                elif item.endswith('.py') and not item.endswith('__init__.py'):
                    # 如果已处理过，跳过
                    if item_path in processed_modules:
                        continue
                    processed_modules.add(item_path)
                    try:
                        # 将文件路径转换为模块路径
                        module_name: str = convert_path_to_module(item_path)
                        # print(module_name)
                        # 使用常规导入方式，这样可以正确处理相对导入
                        module = importlib.import_module(name=module_name)
                        # print(f"导入--》{module_name}")
                        # 查找所有标记为组件的类
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if hasattr(obj, '__component__'):
                                component_classes.append(obj)
                    except Exception as e:
                        logger.error(f"Error importing module {item_path}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {current_dir}: {e}")

# 获取当前进程的容器实例
def get_container() -> Injector:
    # 确保项目根目录在 Python 路径中，以支持模块导入
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    if not hasattr(get_container, "container_instance"):
        get_container.container_instance = injector.Injector(Container())
    return get_container.container_instance