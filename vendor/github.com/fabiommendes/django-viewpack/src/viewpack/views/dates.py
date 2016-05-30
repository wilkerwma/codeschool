from django.views.generic import dates
from viewpack.views.utils import check_mro
from viewpack.utils import lazy, delegate_to_parent
from viewpack.views.base import ChildViewMixin
from viewpack.views.detail import SingleObjectTemplateResponseMixin
from viewpack.views.list import MultipleObjectTemplateResponseMixin


@check_mro
class YearMixin(ChildViewMixin, dates.YearMixin):
    """
    Mixin for views manipulating year-based data.
    """

    year_format = delegate_to_parent('year_format', '%Y')
    year = delegate_to_parent('year')


@check_mro
class MonthMixin(ChildViewMixin, dates.MonthMixin):
    """
    Mixin for views manipulating month-based data.
    """

    month_format = delegate_to_parent('month_format', '%b')
    month = delegate_to_parent('month')


@check_mro
class DayMixin(ChildViewMixin, dates.DayMixin):
    """
    Mixin for views manipulating day-based data.
    """

    day_format = delegate_to_parent('day_format', '%d')
    day = delegate_to_parent('day')


@check_mro
class WeekMixin(ChildViewMixin, dates.WeekMixin):
    """
    Mixin for views manipulating week-based data.
    """

    week_format = delegate_to_parent('week_format', '%U')
    week = delegate_to_parent('week')


@check_mro
class DateMixin(ChildViewMixin, dates.DateMixin):
    """
    Mixin class for views manipulating date-based data.
    """

    date_field = delegate_to_parent('date_field')
    allow_future = delegate_to_parent('allow_future', False)


@check_mro
class ArchiveIndexView(MultipleObjectTemplateResponseMixin,
                       dates.ArchiveIndexView):
    """
    Top-level archive of date-based items.
    """

    allow_empty = delegate_to_parent('allow_empty', False)


@check_mro
class YearArchiveView(MultipleObjectTemplateResponseMixin,
                      dates.YearArchiveView):
    """
    List of objects published in a given year.
    """

    make_object_list = delegate_to_parent('make_object_list', False)


@check_mro
class MonthArchiveView(MultipleObjectTemplateResponseMixin,
                       dates.MonthArchiveView):
    """
    List of objects published in a given month.
    """


@check_mro
class WeekArchiveView(MultipleObjectTemplateResponseMixin,
                      dates.WeekArchiveView):
    """
    List of objects published in a given week.
    """


@check_mro
class DayArchiveView(MultipleObjectTemplateResponseMixin, dates.DayArchiveView):
    """
    List of objects published on a given day.
    """


@check_mro
class TodayArchiveView(MultipleObjectTemplateResponseMixin,
                       dates.TodayArchiveView):
    """
    List of objects published today.
    """


@check_mro
class DateDetailView(SingleObjectTemplateResponseMixin, dates.DateDetailView):
    """
    Detail view of a single object on a single date; this differs from the
    standard DetailView by accepting a year/month/day in the URL.
    """
