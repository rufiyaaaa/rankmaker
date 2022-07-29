import logging
from django.urls import reverse_lazy
from django.views import generic
from .forms import InquiryForm
from django.contrib import messages

from accounts.models import CustomUser

logger = logging.getLogger(__name__)


class IndexView(generic.TemplateView):
    template_name = "entrance/index.html"


class RatingSystemView(generic.TemplateView):
    template_name = "entrance/rating_system.html"


class InquiryView(generic.FormView):
    template_name = "entrance/inquiry.html"
    form_class = InquiryForm
    success_url = reverse_lazy('entrance:inquiry')

    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'メッセージを送信しました。')
        logger.info('Inquiry sent by {}'.format(form.cleaned_data['name']))
        return super().form_valid(form)