import os
import sys
import pytest

HERE = os.path.dirname(__file__)
API_TESTS = os.path.join(HERE, "test_api.py")

errcode = pytest.main([API_TESTS] + sys.argv[1:])
sys.exit(errcode)
