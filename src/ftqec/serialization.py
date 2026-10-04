"""Strict JSON-native serialization at public API boundaries."""
import json


def json_native(value):
    return json.loads(json.dumps(value, allow_nan=False))
