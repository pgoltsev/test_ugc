class FormWidgetMixin:
    """Миксин позволяет в админке задавать виджеты для указанных полей."""

    def formfield_for_dbfield(self, db_field, **kwargs):
        # noinspection PyUnresolvedReferences
        formfield = super().formfield_for_dbfield(db_field, **kwargs)

        widgets = getattr(self, 'form_widgets', {})
        widget_data = widgets.get(db_field.name)
        if widget_data:
            if isinstance(widget_data, tuple):
                widget_cls, keys = widget_data
            else:
                widget_cls = widget_data
                keys = ()

            keys = set(keys)
            keys.add('attrs')

            formfield.widget = widget_cls(**{
                key: getattr(formfield.widget, key)
                for key in keys
            })

        return formfield
