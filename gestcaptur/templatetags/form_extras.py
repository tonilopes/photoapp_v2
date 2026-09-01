# gestcaptur/templatetags/form_extras.py
from django import template

register = template.Library()

@register.filter
def get_field_label(form, field_name):
    """Retorna o label de um campo do formulário"""
    if field_name in form.fields:
        return form.fields[field_name].label
    return field_name.replace('_', ' ').title()