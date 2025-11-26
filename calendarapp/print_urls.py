import os
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0])

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "truetalk.settings")
import django
django.setup()
from django.urls import get_resolver

def walk(patterns, prefix=""):
    for p in patterns:
        print(prefix + repr(p))
        if hasattr(p, "url_patterns"):
            walk(p.url_patterns, prefix + "  ")

r = get_resolver(None)
walk(r.url_patterns)
