import time

import pytest

_last_test_time = 0

@pytest.fixture(autouse=True)
def throttle_simulation_tests():
  global _last_test_time
  if _last_test_time > 0:
      elapsed = time.time() - _last_test_time
      if elapsed < 60:
          time.sleep(60 - elapsed)
  _last_test_time = time.time()
