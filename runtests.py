#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    # Configure path and django settings module
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/tests")
    os.environ["DJANGO_SETTINGS_MODULE"] = "test_settings"
    django.setup()

    # Initialise test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    # Run tests and report failures
    failures = test_runner.run_tests(["tests"])
    sys.exit(bool(failures))
