"""Oscar Odin.

Odin Resources and mappings to Oscar models.
"""
import os
import sys


def django_manage():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
