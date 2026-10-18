
from django import forms
from django.utils import timezone
from .models import Period


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ["start_date", "end_date", "notes"]

        widgets = {
            "start_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "How are you feeling today? (optional)"
                }
            ),
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")

        if start_date and start_date > timezone.localdate():
            raise forms.ValidationError(
                "The period start date cannot be in the future."
            )

        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")

        if end_date and end_date > timezone.localdate():
            raise forms.ValidationError(
                "The period end date cannot be in the future."
            )

        return end_date

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "The end date cannot be before the start date."
            )

        return cleaned_data
