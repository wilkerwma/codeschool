from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register)
from .models import FormQuestion


class MyPageModelAdmin(ModelAdmin):
    model = FormQuestion
    menu_label = 'Page Model'  # ditch this to use verbose_name_plural from model
    menu_icon = 'date'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    list_display = ('title', 'live')
    list_filter = ('live',)
    search_fields = ('title',)

# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(MyPageModelAdmin)