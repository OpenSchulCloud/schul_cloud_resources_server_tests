import os
import sys

HERE = os.path.dirname(__file__)

if __name__ == "__main__":
    import pytest
    pytest.main([HERE] + sys.argv[1:])