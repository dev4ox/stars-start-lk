from django.forms.widgets import SelectMultiple
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.html import format_html, json_script


class ReadOnlySelectMultiple(SelectMultiple):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['disabled'] = 'disabled'

    def render(self, name, value, attrs=None, renderer=None):
        return ""


class CustomFilteredSelectMultiple(FilteredSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        script = """
           <script type="text/javascript">
               var select = document.getElementById({name_json});
               if (select) {
                   for (var i = 0; i < select.options.length; i++) {
                       var option = select.options[i];
                       option.text = option.text + " (" + option.value + ")";
                   }
               }
           </script>
           """
        name_json = json_script("id_" + name)
        output += format_html(script, name_json=name_json)
        return output
