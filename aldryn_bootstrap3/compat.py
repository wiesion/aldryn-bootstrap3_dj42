from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import html_safe, format_html
from django.utils.safestring import mark_safe


@html_safe
class SubWidget(object):
    """
    This class is only needed for Django >= 1.11 compatibility

    Some widgets are made of multiple HTML elements -- namely, RadioSelect.
    This is a class that represents the "inner" HTML element of a widget.
    """

    def __init__(self, parent_widget, name, value, attrs, choices):
        self.parent_widget = parent_widget
        self.name, self.value = name, value
        self.attrs, self.choices = attrs, choices

    def __str__(self):
        args = [self.name, self.value, self.attrs]
        if self.choices:
            args.append(self.choices)
        return self.parent_widget.render(*args)


@html_safe
class ChoiceInput(SubWidget):
    """
    This class is only needed for Django >= 1.11 compatibility

    An object used by ChoiceFieldRenderer that represents a single
    <input type='$input_type'>.
    """

    input_type = None  # Subclasses must define this

    def __init__(self, name, value, attrs, choice, index):
        self.name = name
        self.value = value
        self.attrs = attrs
        self.choice_value = force_text(choice[0])
        self.choice_label = force_text(choice[1])
        self.index = index
        if "id" in self.attrs:
            self.attrs["id"] += "_%d" % self.index

    def __str__(self):
        return self.render()

    def render(self, name=None, value=None, attrs=None):
        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ""
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return format_html("<label{}>{} {}</label>", label_for, self.tag(attrs), self.choice_label)

    def is_checked(self):
        return self.value == self.choice_value

    def tag(self, attrs=None):
        attrs = attrs or self.attrs
        final_attrs = dict(attrs, type=self.input_type, name=self.name, value=self.choice_value)
        if self.is_checked():
            final_attrs["checked"] = "checked"
        return format_html("<input{} />", flatatt(final_attrs))

    @property
    def id_for_label(self):
        return self.attrs.get("id", "")


class CheckboxChoiceInput(ChoiceInput):
    """
    This class is only needed for Django >= 1.11 compatibility
    """

    input_type = "checkbox"

    def __init__(self, *args, **kwargs):
        super(CheckboxChoiceInput, self).__init__(*args, **kwargs)
        self.value = set(force_text(v) for v in self.value)

    def is_checked(self):
        return self.choice_value in self.value


class RadioChoiceInput(ChoiceInput):
    input_type = "radio"

    def __init__(self, *args, **kwargs):
        super(RadioChoiceInput, self).__init__(*args, **kwargs)
        self.value = force_text(self.value)


@html_safe
class ChoiceFieldRenderer(object):
    """
    This class is only needed for Django >= 1.11 compatibility

    An object used by RadioSelect to enable customization of radio widgets.
    """

    choice_input_class = None
    outer_html = "<ul{id_attr}>{content}</ul>"
    inner_html = "<li>{choice_value}{sub_widgets}</li>"

    def __init__(self, name, value, attrs, choices):
        self.name = name
        self.value = value
        self.attrs = attrs
        self.choices = choices

    def __getitem__(self, idx):
        return list(self)[idx]

    def __iter__(self):
        for idx, choice in enumerate(self.choices):
            yield self.choice_input_class(self.name, self.value, self.attrs.copy(), choice, idx)

    def __str__(self):
        return self.render()

    def render(self):
        """
        This class is only needed for Django >= 1.11 compatibility

        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        id_ = self.attrs.get("id")
        output = []
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus["id"] += "_{}".format(i)
                sub_ul_renderer = self.__class__(
                    name=self.name, value=self.value, attrs=attrs_plus, choices=choice_label
                )
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(
                    format_html(self.inner_html, choice_value=choice_value, sub_widgets=sub_ul_renderer.render())
                )
            else:
                w = self.choice_input_class(self.name, self.value, self.attrs.copy(), choice, i)
                output.append(format_html(self.inner_html, choice_value=force_text(w), sub_widgets=""))
        return format_html(
            self.outer_html, id_attr=format_html(' id="{}"', id_) if id_ else "", content=mark_safe("\n".join(output))
        )


class RadioFieldRenderer(ChoiceFieldRenderer):
    """
    This class is only needed for Django >= 1.11 compatibility
    """

    choice_input_class = RadioChoiceInput


class CheckboxFieldRenderer(ChoiceFieldRenderer):
    """
    This class is only needed for Django >= 1.11 compatibility
    """

    choice_input_class = CheckboxChoiceInput


class RendererMixin(object):
    """
    This class is only needed for Django >= 1.11 compatibility
    """

    renderer = None  # subclasses must define this
    _empty_value = None

    def __init__(self, *args, **kwargs):
        # Override the default renderer if we were passed one.
        renderer = kwargs.pop("renderer", None)
        if renderer:
            self.renderer = renderer
        super(RendererMixin, self).__init__(*args, **kwargs)

    def subwidgets(self, name, value, attrs=None):
        for widget in self.get_renderer(name, value, attrs):
            yield widget

    def get_renderer(self, name, value, attrs=None):
        """Returns an instance of the renderer."""
        if value is None:
            value = self._empty_value
        final_attrs = self.build_attrs(attrs)
        return self.renderer(name, value, final_attrs, self.choices)

    def render(self, name, value, attrs=None):
        return self.get_renderer(name, value, attrs).render()

    def id_for_label(self, id_):
        # Widgets using this RendererMixin are made of a collection of
        # subwidgets, each with their own <label>, and distinct ID.
        # The IDs are made distinct by a "_X" suffix, where X is the zero-based
        # index of the choice field. Thus, the label for the main widget should
        # reference the first subwidget, hence the "_0" suffix.
        if id_:
            id_ += "_0"
        return id_
