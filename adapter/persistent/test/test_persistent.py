from application.port.outbound.test_case import TestCase
from common.core.container.annotate import component
from common.core.errors.business_exception import BusinessException
from common.core.errors.business_error_code import GeneratorErrorCode

@component
class TestPersistent(TestCase):

    def __init__(self):
        print('dd_init')

    def test_del(self):
        print("test_del")

    async def test_add(self):
        print("test_add")
        raise BusinessException(error_code=GeneratorErrorCode.NO_APIKEY_FOUND, dynamics_message="test")