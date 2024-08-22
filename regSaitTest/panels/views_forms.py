# python lib
from typing import Type

# pip lib
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.db import SessionStore

# my lib
from .decorators.func import panels_form_sub_data


class AddOrGetDataSession:
    def __init__(self, session, parse: bool = False, **kwargs):
        self.session = session
        self.parse = parse
        self.kwargs = kwargs

    def __new__(cls, session, parse: bool = False, **kwargs) -> Type[SessionStore] | "AddOrGetDataSession":
        instance = super().__new__(cls)

        instance.__init__(session, parse, **kwargs)

        default_value = {
            "form_name": None,
            "form_widgets_name": None,
            "url_redirect": None,
            "model_name": None,
            "model_list_param_name": None,
            "model_save_commit": None,
            "model_link_field_value": None,
            "html_vars": None,
        }

        if parse:
            return cls.__parser(
                session=session,
                instance=instance,
                default_value=default_value,
            )

        for name, value in default_value.items():
            try:
                session[name] = kwargs[name]

            except KeyError:
                session[name] = value

        return session

    @classmethod
    def __parser(cls, session, instance, default_value: dict) -> "AddOrGetDataSession":
        for name, value in default_value.items():
            try:
                setattr(instance, name, session[name])

            except KeyError:
                setattr(instance, name, value)

        return instance


@panels_form_sub_data
@login_required
def panels_form_details(request, id_):
    data = AddOrGetDataSession(
        session=request.session,
        parse=True,
    )

    if data.model_name is not None:
        model_kwargs = {}

        for param_name in data.model_list_param_name:
            model_kwargs[param_name] = id_

        model = request.models[data.model_name].objects.get(**model_kwargs)

    else:
        model = None

    form = request.forms_change[data.form_name](instance=model)

    if data.html_vars is not None:
        request.context["title"] = data.html_vars["title"]
        request.context["h2_tag"] = data.html_vars["h2_tag"]

    request.context["form"] = form
    request.context["url_redirect"] = data.url_redirect

    return render(request, "form_details.html", request.context)


@panels_form_sub_data
@login_required
def panels_form_change(request, id_):
    data = AddOrGetDataSession(
        session=request.session,
        parse=True,
    )

    if data.model_name is not None and request.path.endswith("/edit/"):
        model_kwargs = {}

        for param_name in data.model_list_param_name:
            model_kwargs[param_name] = id_

        model = request.models[data.model_name].objects.get(**model_kwargs)

    if request.method == "POST":
        if data.model_name is not None and request.path.endswith("/edit/"):
            form = request.forms_change[data.form_name](request.POST, request.FILES, instance=model)

        else:
            form = request.forms_change[data.form_name](request.POST, request.FILES)

        if form.is_valid():
            if data.model_save_commit:
                form.save()

            else:
                model = form.save(commit=False)

                if data.model_link_field_value is not None:
                    for model_field, to_model_fields in data.model_link_field_value.items():
                        if "." in to_model_fields:
                            len_to_model_fields = len(to_model_fields.split("."))
                            to_model_fields = to_model_fields.split(".")

                            if len_to_model_fields == 2:
                                setattr(
                                    model,
                                    model_field,
                                    getattr(
                                        getattr(
                                            model,
                                            to_model_fields[0]
                                        ),
                                        to_model_fields[1]
                                    )
                                )

                model.save()

            form.save_m2m()

            return redirect(data.url_redirect)

    else:
        if data.model_name is not None and request.path.endswith("/edit/"):
            form = request.forms_change[data.form_name](instance=model)

        else:
            form = request.forms_change[data.form_name]()

        if data.form_widgets_name is not None:
            for field, widget_name in data.form_widgets_name.items():
                form.fields[field].widget = request.form_widgets[widget_name]

    if data.html_vars is not None:
        request.context["title"] = data.html_vars["title"]
        request.context["h2_tag"] = data.html_vars["h2_tag"]

    request.context["form"] = form
    request.context["url_redirect"] = data.url_redirect

    return render(request, "form_change.html", request.context)


@panels_form_sub_data
@login_required
def panels_form_delete(request, id_):
    data = AddOrGetDataSession(
        session=request.session,
        parse=True,
    )

    if data.model_name is not None:
        model_kwargs = {}

        for param_name in data.model_list_param_name:
            model_kwargs[param_name] = id_

        model = request.models[data.model_name].objects.get(**model_kwargs)

    if request.method == "POST":
        model.delete()

        return redirect(data.url_redirect)

    if data.html_vars is not None:
        request.context["title"] = data.html_vars["title"]
        request.context["h2_tag"] = data.html_vars["h2_tag"]

    request.context["url_redirect"] = data.url_redirect

    return render(request, "form_delete.html", request.context)
