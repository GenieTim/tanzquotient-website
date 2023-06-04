import logging
from datetime import date

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.http import Http404, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from courses.forms import UserEditForm, create_initial_from_user
from courses.utils import merge_duplicate_users, find_duplicate_users
from tq_website import settings
from utils.plots import plot_figure
from utils.tables.table_view_or_export import table_view_or_export
from . import services, figures
from .forms.subscribe_form import SubscribeForm
from .models import (
    Course,
    Style,
    Offering,
    OfferingType,
    Subscribe,
    IrregularLesson,
    RegularLessonException,
)
from .services.data.teachers_overview import get_teachers_overview_data
from .utils import course_filter

log = logging.getLogger("tq")


# Create your views here.


def course_list(
    request, subscription_type="all", style_name="all", show_preview=False
) -> HttpResponse:
    template_name = "courses/list.html"

    filter_styles = Style.objects.filter(filter_enabled=True)

    def matches_filter(c: Course) -> bool:
        return course_filter(
            c, show_preview, subscription_type, style_name, filter_styles
        )

    offerings = services.get_offerings_to_display(show_preview).prefetch_related(
        "period__cancellations",
        "course_set__type",
        "course_set__period__cancellations",
        "course_set__regular_lessons",
        "course_set__room__address",
        "course_set__room__translations",
        Prefetch(
            "course_set__irregular_lessons",
            queryset=IrregularLesson.objects.order_by("date", "time_from"),
        ),
        Prefetch(
            "course_set__regular_lessons__exceptions",
            queryset=RegularLessonException.objects.order_by("date"),
        ),
        Prefetch(
            "course_set__subscriptions",
            queryset=Subscribe.objects.active(),
            to_attr="active_subscriptions",
        ),
        "course_set__subscriptions",
    )

    c_offerings = []
    for offering in offerings:
        offering_sections = services.get_sections(offering, matches_filter)

        if offering_sections:
            c_offerings.append(
                {
                    "offering": offering,
                    "sections": offering_sections,
                }
            )

    context = {
        "offerings": c_offerings,
        "filter": {
            "styles": {
                "available": filter_styles,
                "selected": style_name,
            },
            "subscription_type": subscription_type,
        },
    }
    return render(request, template_name, context)


def archive(request: HttpRequest) -> HttpResponse:
    template_name = "courses/archive.html"
    context = dict()
    return render(request, template_name, context)


@staff_member_required
def course_list_preview(request) -> HttpResponse:
    return course_list(request, show_preview=True)


def offering_by_id(request: HttpRequest, offering_id: int) -> HttpResponse:
    template_name = "courses/offering.html"
    offering = get_object_or_404(Offering.objects, id=offering_id)
    if not offering.is_public():
        raise Http404()
    context = {"offering": offering, "sections": services.get_sections(offering)}
    return render(request, template_name, context)


def course_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    context = {
        "menu": "courses",
        "course": get_object_or_404(Course.objects, id=course_id),
        "user": request.user,
    }
    return render(request, "courses/course_detail.html", context)


@login_required
def subscribe_form(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course.objects, id=course_id)

    # If user already signed up or sign up not possible: redirect to course detail
    if (
        course.subscriptions.filter(user=request.user).exists()
        or (not course.is_subscription_allowed() and not request.user.is_staff)
        or not course.has_free_places
    ):
        return redirect("courses:course_detail", course_id=course_id)

    # If user has overdue payments -> block subscribing to new courses
    if request.user.profile.subscriptions_with_overdue_payment():
        return render(
            request,
            "courses/overdue_payments.html",
            dict(
                email_address=settings.EMAIL_ADDRESS_FINANCES,
                payment_account=settings.PAYMENT_ACCOUNT["default"],
            ),
        )

    # Get form
    form_data = request.POST if request.method == "POST" else None
    form = SubscribeForm(user=request.user, course=course, data=form_data)

    # Sign up user for course if form is valid
    if form.is_valid():
        subscription = services.subscribe(course, request.user, form.cleaned_data)
        context = {
            "course": course,
            "subscription": subscription,
        }
        return render(request, "courses/course_subscribe_status.html", context=context)

    # Render sign up form

    past_partners = sorted(
        list(
            {
                (subscribe.partner.get_full_name(), subscribe.partner.email)
                for subscribe in request.user.subscriptions.all()
                if subscribe.partner
            }
        )
    )

    context = {
        "course": course,
        "form": form,
        "past_partners": past_partners,
    }
    return render(request, "courses/course_subscribe_form.html", context)


@staff_member_required
def confirmation_check(request: HttpRequest) -> HttpResponse:
    template_name = "courses/confirmation_check.html"
    context = {}

    context.update(
        {
            "subscriptions": Subscribe.objects.accepted()
            .select_related()
            .filter(confirmations__isnull=True)
            .all()
        }
    )
    return render(request, template_name, context)


@staff_member_required
def duplicate_users(request: HttpRequest) -> HttpResponse:
    template_name = "courses/duplicate_users.html"
    context = {}
    users = []
    user_aliases = dict()

    # if this is a POST request we need to process the form data
    if (
        request.method == "POST"
        and "post" in request.POST
        and request.POST["post"] == "yes"
    ):
        duplicates_ids = request.session["duplicates"]
        to_merge = dict()
        for primary_id, aliases_ids in duplicates_ids.items():
            to_merge_aliases = []
            for alias_id in aliases_ids:
                key = "{}-{}".format(primary_id, alias_id)
                if key in request.POST and request.POST[key] == "yes":
                    to_merge_aliases.append(alias_id)
            if to_merge_aliases:
                to_merge[primary_id] = to_merge_aliases
        log.info(to_merge)
        merge_duplicate_users(to_merge)
    else:
        duplicates = find_duplicate_users()
        for primary, aliases in duplicates.items():
            users.append(User.objects.get(id=primary))
            user_aliases[primary] = list(User.objects.filter(id__in=aliases))

        # for use when form is submitted
        request.session["duplicates"] = duplicates

    context.update({"users": users, "user_aliases": user_aliases})
    return render(request, template_name, context)


def offering_time_chart_dict(offering: Offering) -> dict:
    traces = []
    for c in offering.course_set.reverse().all():
        trace = dict()
        trace["name"] = c.name
        values = dict()
        for s in c.subscriptions.all():
            key = str(s.date.date())
            values[key] = values.get(key, 0) + 1

        tuples = [(x, y) for x, y in values.items()]

        trace["x"] = [x for x, _ in tuples]
        trace["y"] = [y for _, y in tuples]

        traces.append(trace)

    trace_total = dict()
    trace_total["x"] = []
    trace_total["y"] = []
    counter = 0
    last = None

    for s in (
        Subscribe.objects.filter(course__offering__id=offering.id)
        .order_by("date")
        .all()
    ):
        if last is None:
            last = s.date.date()
        if s.date.date() == last:
            counter += 1
        else:
            # save temp
            print("add counter {}".format(counter))
            trace_total["x"].append(str(last))
            trace_total["y"].append(counter)
            counter += 1
            last = s.date.date()
    if last is not None:
        trace_total["x"].append(str(last))
        trace_total["y"].append(counter)

    print(trace_total["x"])
    print(trace_total["y"])

    return {
        "traces": traces,
        "trace_total": trace_total,
        "trace_total": trace_total,
    }


@staff_member_required
def teachers_overview(request: HttpRequest) -> HttpResponse:
    return table_view_or_export(
        request,
        _("Teachers overview"),
        "courses:teachers_overview",
        get_teachers_overview_data(),
    )


@staff_member_required
def subscription_overview(request: HttpRequest) -> HttpResponse:
    figure_types = dict(
        status=dict(
            title=_("By subscription status"), plot=figures.offering_state_status
        ),
        affiliation=dict(
            title=_("By affiliation"), plot=figures.offering_by_student_status
        ),
        matching=dict(
            title=_("By matching states"), plot=figures.offering_matching_status
        ),
        lead_follow=dict(
            title=_("By lead and follow"), plot=figures.offering_lead_follow_couple
        ),
    )
    figure_type: str = (
        request.GET["figure_type"] if "figure_type" in request.GET else "status"
    )
    return render(
        request,
        "courses/auth/subscription_overview.html",
        dict(
            figure_type=figure_type,
            figure_types=[(k, v["title"]) for k, v in figure_types.items()],
            plots={
                offering_type: plot_figure(
                    figure_types[figure_type]["plot"](offering_type)
                )
                for offering_type in [OfferingType.REGULAR, OfferingType.IRREGULAR]
            },
        ),
    )


@staff_member_required
def offering_overview(request: HttpRequest, offering_id: int) -> HttpResponse:
    template_name = "courses/auth/offering_overview.html"
    context = {}

    offering = Offering.objects.get(id=offering_id)

    context["offering"] = offering
    context["place_chart"] = plot_figure(
        figures.courses_confirmed_matched_lead_follow_free(offering)
    )
    context["time_chart"] = offering_time_chart_dict(offering)
    return render(request, template_name, context)


@login_required
def user_courses(request: HttpRequest) -> HttpResponse:
    template_name = "user/user_courses.html"
    context = {
        "user": request.user,
        "payment_account": settings.PAYMENT_ACCOUNT["default"],
    }
    return render(request, template_name, context)


@login_required
def user_profile(request: HttpRequest) -> HttpResponse:
    template_name = "user/profile.html"
    context = {"user": request.user}
    return render(request, template_name, context)


@method_decorator(login_required, name="dispatch")
class ProfileView(FormView):
    template_name = "courses/auth/profile.html"
    form_class = UserEditForm

    success_url = reverse_lazy("edit_profile")

    def get_initial(self) -> dict:
        initial = create_initial_from_user(self.request.user)
        return initial

    def get_context_data(self, **kwargs) -> dict:
        # Call the base implementation first to get a context
        context = super(ProfileView, self).get_context_data(**kwargs)

        user = self.request.user
        context["is_teacher"] = user.profile.is_teacher()
        context["is_board_member"] = user.profile.is_board_member()
        context["is_profile_complete"] = user.profile.is_complete()
        context["profile_missing_values"] = user.profile.missing_values()
        return context

    def form_valid(self, form) -> HttpResponse:
        services.update_user(self.request.user, form.cleaned_data)
        return super(ProfileView, self).form_valid(form)


@login_required
def change_password(request: HttpRequest) -> HttpResponse:
    success = True
    initial = True
    if request.method == "POST":
        initial = False
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
        else:
            success = False
    else:
        form = PasswordChangeForm(request.user)

    return render(
        request,
        "account/change_password.html",
        {
            "form": form,
            "success": success,
            "initial": initial,
        },
    )


@staff_member_required
def export_summary(request: HttpRequest) -> HttpResponse:
    from courses import services

    return services.export_summary("csv")


@staff_member_required
def export_summary_excel(request: HttpRequest) -> HttpResponse:
    from courses import services

    return services.export_summary("xlsx")


@staff_member_required
def export_offering_summary(request: HttpRequest, offering_id: int) -> HttpResponse:
    from courses import services

    return services.export_summary(
        "csv", [Offering.objects.filter(pk=offering_id).first()]
    )


@staff_member_required
def export_offering_summary_excel(
    request: HttpRequest, offering_id: int
) -> HttpResponse:
    from courses import services

    return services.export_summary(
        "xlsx", [Offering.objects.filter(pk=offering_id).first()]
    )
