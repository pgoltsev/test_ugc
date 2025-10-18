from django.db.models import Model
from django.template.loader import render_to_string
from django.urls import reverse


def get_admin_url_name(obj: Model, view_name: str) -> str:
    """
    Return admin URL name of the given object for the given view.
    :param obj: Object.
    :param view_name: View name, e.g. 'change', 'list', etc.
    :return: URL name that can be passed to the 'reverse' function.
    """
    # noinspection PyUnresolvedReferences,PyProtectedMember
    model_meta = obj.__class__._meta
    app_name = model_meta.app_label
    model_name = model_meta.object_name.lower()
    return f'admin:{app_name}_{model_name}_{view_name}'


def render_admin_change_link(obj: Model, title: str = None) -> str:
    """
    Render an HTML link to the given object.
    :param obj: Object.
    :param title: Title. If not set the object will be converted to a string.
    :return: HTML link to the admin change page for the given object.
    """
    return render_to_string('admin/ugc/list_item_extra.html', {
        'url': reverse(
            get_admin_url_name(obj, 'change'),
            args=(obj.pk,),
        ),
        'title': str(obj) if title is None else title,
        'obj': obj,
    })
