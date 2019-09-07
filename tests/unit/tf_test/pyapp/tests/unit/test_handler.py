
import importlib.util
from unittest import TestCase
from pathlib import Path


class TestHandler(TestCase):
    """Loads module without __init__"""
    def setUp(self):
        file_to_test = 'app.py'
        path = Path(__file__, '..', '..', '..', 'src', file_to_test)
        print(path)
        self.assertTrue(path.exists())
        spec = importlib.util.spec_from_file_location(
            file_to_test,
            path
        )
        self.module = importlib.util.module_from_spec(spec)
        self.module.__spec__.loader.exec_module(self.module)

    def test_handler_returns_zero(self):
        event = {'target': '1'}
        context = 0
        result = self.module.handler(event, context)
        self.assertEqual(result, 0)
