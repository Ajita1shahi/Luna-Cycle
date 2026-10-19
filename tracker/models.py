
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Period(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Period starting {self.start_date}"


class SymptomEntry(models.Model):

    MOOD_CHOICES = [
        ("happy", "Happy"),
        ("calm", "Calm"),
        ("energetic", "Energetic"),
        ("sad", "Sad"),
        ("anxious", "Anxious"),
        ("irritable", "Irritable"),
        ("tired", "Tired"),
        ("emotional", "Emotional"),
    ]

    FLOW_CHOICES = [
        ("none", "No period"),
        ("spotting", "Spotting"),
        ("light", "Light"),
        ("medium", "Medium"),
        ("heavy", "Heavy"),
    ]

    ENERGY_CHOICES = [
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="symptom_entries"
    )

    date = models.DateField()

    mood = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        blank=True
    )

    flow = models.CharField(
        max_length=20,
        choices=FLOW_CHOICES,
        default="none"
    )

    pain_level = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ],
        help_text="Rate your pain from 0 (none) to 10 (severe)."
    )

    energy_level = models.CharField(
        max_length=20,
        choices=ENERGY_CHOICES,
        blank=True
    )

    symptoms = models.TextField(
        blank=True,
        help_text="For example: cramps, headache, bloating, or fatigue."
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"],
                name="unique_symptom_entry_per_user_date"
            )
        ]

    def __str__(self):
        return f"Symptom journal - {self.date}"
