#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    # Configure path and django settings module
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/tests")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
