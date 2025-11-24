from django import template
import markdown as md

register = template.Library()

@register.filter
def markdownify(value):
    if not value:
        return ""
    return md.markdown(
        value,
        extensions=[
            "extra",
            "nl2br",
        ],
    )
