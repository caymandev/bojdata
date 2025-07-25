#!/usr/bin/env python3
"""Explore bojdata package structure and available functions"""

import bojdata
import inspect

print("=== Exploring bojdata package ===")
print(f"Package version: {bojdata.__version__ if hasattr(bojdata, '__version__') else 'Unknown'}")
print(f"Package location: {bojdata.__file__}")
print()

print("Available attributes and functions:")
for name in dir(bojdata):
    if not name.startswith('_'):
        obj = getattr(bojdata, name)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                print(f"  {name}{sig}")
            except:
                print(f"  {name}()")
        else:
            print(f"  {name}: {type(obj).__name__}")
print()

# Try to find main API classes/functions
if hasattr(bojdata, 'Fred') or hasattr(bojdata, 'BOJ'):
    print("Main API class found!")
    api_class = getattr(bojdata, 'Fred', None) or getattr(bojdata, 'BOJ', None)
    print(f"API Class: {api_class}")
    print("Methods:")
    for method in dir(api_class):
        if not method.startswith('_'):
            print(f"  - {method}")