from django.db import models
from django.conf import settings
from apps.tenants.models import BaseEntity, Company, Branch

class Lead(BaseEntity):
    LEAD_SOURCES = [
        ('WEBSITE', 'Website'),
        ('REFERRAL', 'Referral'),
        ('FACEBOOK', 'Facebook'),
        ('INSTAGRAM', 'Instagram'),
        ('LINKEDIN', 'LinkedIn'),
        ('GOOGLE_ADS', 'Google Ads'),
        ('TRADE_SHOW', 'Trade Show'),
        ('MANUAL', 'Manual Entry'),
        ('IMPORT', 'Import'),
        ('API', 'API'),
    ]

    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified'),
        ('LOST', 'Lost'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, null=True, blank=True)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, null=True, blank=True)
    source = models.CharField(max_length=50, choices=LEAD_SOURCES, default='MANUAL')
    industry = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, default='JO')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='NEW')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='MEDIUM')
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_leads')

    def __str__(self):
        return self.name

class Opportunity(BaseEntity):
    STAGE_CHOICES = [
        ('NEW', 'New'),
        ('QUALIFIED', 'Qualified'),
        ('PROPOSAL', 'Proposal'),
        ('NEGOTIATION', 'Negotiation'),
        ('WON', 'Won'),
        ('LOST', 'Lost'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    name = models.CharField(max_length=255)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='NEW')
    probability = models.IntegerField(default=10) # 0 to 100
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)
    close_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_opportunities')

    def __str__(self):
        return self.name

class Activity(BaseEntity):
    ACTIVITY_TYPES = [
        ('CALL', 'Call'),
        ('MEETING', 'Meeting'),
        ('TASK', 'Task'),
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('NOTE', 'Note'),
        ('FOLLOW_UP', 'Follow-Up'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()
    due_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.activity_type} - {self.description[:30]}"

class Task(BaseEntity):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ESCALATED', 'Escalated'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='crm_tasks')
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='MEDIUM')

    def __str__(self):
        return self.title

class Meeting(BaseEntity):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, null=True, blank=True)
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='crm_meetings')

    def __str__(self):
        return self.title

class Quotation(BaseEntity):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('SENT', 'Sent'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    DISCOUNT_TYPES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed'),
    ]

    quotation_number = models.CharField(max_length=100, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=50, default='RETAIL') # RETAIL, WHOLESALE
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='PERCENTAGE')
    discount_value = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.1600)
    total_amount = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)
    expiration_date = models.DateField(null=True, blank=True)
    terms_conditions = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.quotation_number

class QuotationLine(BaseEntity):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lines')
    item_name = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=15, decimal_places=4, default=1.0000)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)
    discount = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000) # Line discount
    line_total = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)

    def __str__(self):
        return f"{self.item_name} ({self.qty})"

class SalesOrder(BaseEntity):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    FULFILLMENT_STATUS = [
        ('UNFULFILLED', 'Unfulfilled'),
        ('PARTIALLY_FULFILLED', 'Partially Fulfilled'),
        ('FULFILLED', 'Fulfilled'),
    ]

    INVOICE_STATUS = [
        ('UNINVOICED', 'Uninvoiced'),
        ('PARTIALLY_INVOICED', 'Partially Invoiced'),
        ('INVOICED', 'Invoiced'),
    ]

    DELIVERY_STATUS = [
        ('PENDING', 'Pending'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
    ]

    order_number = models.CharField(max_length=100, unique=True)
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')
    fulfillment_status = models.CharField(max_length=50, choices=FULFILLMENT_STATUS, default='UNFULFILLED')
    invoice_status = models.CharField(max_length=50, choices=INVOICE_STATUS, default='UNINVOICED')
    delivery_status = models.CharField(max_length=50, choices=DELIVERY_STATUS, default='PENDING')
    total_amount = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)

    def __str__(self):
        return self.order_number

class OrderLine(BaseEntity):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines')
    item_name = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=15, decimal_places=4, default=1.0000)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)
    line_total = models.DecimalField(max_digits=15, decimal_places=4, default=0.0000)

    def __str__(self):
        return f"{self.item_name} ({self.qty})"

class SalesCommunication(BaseEntity):
    CHANNELS = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('IN_APP', 'In-App'),
    ]

    customer_name = models.CharField(max_length=255)
    channel = models.CharField(max_length=50, choices=CHANNELS)
    subject = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.channel} to {self.customer_name}"
