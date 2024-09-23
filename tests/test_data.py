import unittest

from compressa.perf.data.models import Deploy


class TestData(unittest.TestCase):
    def setUp(self):
        print('setUp')

    def tearDown(self):
        print('tearDown')

    def test_deploy(self):
        deploy = Deploy(
            deploy_id=1,
            model_name="llama3",
            hardware="A100-40GB",
            context_length=4096,
            quantization="int8",
        )
