from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring_without_page(context):
    """Return the current GET querystring (without 'page'), with a trailing '&' if non-empty."""
    request = context.get('request')
    if not request:
        return ''
    params = request.GET.copy()
    params.pop('page', None)
    encoded = params.urlencode()
    return f"{encoded}&" if encoded else ''
