from __future__ import annotations

import json

from django import template

register = template.Library()


@register.filter
def attr(obj, name: str):
    value = getattr(obj, name, "")
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return value
