from django import template

register = template.Library()


@register.inclusion_tag('includes/form_field.html')
def form_field(field, col_class='col-md-6'):
    """Form alanı için tekrarlayan HTML kodunu azaltır"""
    return {
        'field': field,
        'col_class': col_class,
    }


@register.inclusion_tag('includes/card_wrapper.html')
def card_wrapper(title, extra_classes=''):
    """Card wrapper için tekrarlayan HTML kodunu azaltır"""
    return {
        'title': title,
        'extra_classes': extra_classes,
    }


@register.inclusion_tag('includes/delete_confirm.html')
def delete_confirm(object_name, object_display, cancel_url, warning_message='', button_text='Evet, Sil'):
    """Silme onay sayfası için tekrarlayan HTML kodunu azaltır"""
    return {
        'object_name': object_name,
        'object_display': object_display,
        'cancel_url': cancel_url,
        'warning_message': warning_message,
        'button_text': button_text,
    }

