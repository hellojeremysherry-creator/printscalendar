from django.db import models

class SaleEvent(models.Model):
    STATUS_CHOICES = [
        ('researching', 'Researching'),
        ('preparing', 'Preparing'),
        ('bidding', 'Bidding'),
        ('passed', 'Passed'),
    ]

    title = models.CharField(max_length=200)
    auction_house = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='researching',
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date', 'title']

    def __str__(self):
        return f"{self.title} ({self.start_date})"
