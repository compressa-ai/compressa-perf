import unittest
import sqlite3
from compressa.perf.inference import InferenceRunner
from compressa.perf.db import DB_NAME

class TestData(unittest.TestCase):
    def setUp(self):
        print('setUp')

    def tearDown(self):
        print('tearDown')

    def test_inference(self):
        with sqlite3.connect(DB_NAME) as conn:
            runner = InferenceRunner(
                conn=conn,
                openai_api_key="",
                openai_url="",
                model_name="Compressa",
            )
