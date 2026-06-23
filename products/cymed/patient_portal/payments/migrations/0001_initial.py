import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PatientInvoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('cycom_invoice_id', models.CharField(db_index=True, max_length=255)),
                ('invoice_number', models.CharField(db_index=True, max_length=100, unique=True)),
                ('invoice_type', models.CharField(
                    choices=[
                        ('consultation', 'Consultation'),
                        ('procedure', 'Procedure'),
                        ('lab', 'Lab'),
                        ('imaging', 'Imaging'),
                        ('pharmacy', 'Pharmacy'),
                        ('admission', 'Admission'),
                        ('other', 'Other'),
                    ],
                    default='consultation',
                    max_length=20,
                )),
                ('provider_name', models.CharField(max_length=255)),
                ('service_date', models.DateField(blank=True, null=True)),
                ('amount_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('amount_covered_insurance', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('amount_patient_due', models.DecimalField(decimal_places=2, max_digits=12)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('partially_paid', 'Partially Paid'),
                        ('paid', 'Paid'),
                        ('overdue', 'Overdue'),
                        ('cancelled', 'Cancelled'),
                        ('refunded', 'Refunded'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('due_date', models.DateField(blank=True, null=True)),
                ('pdf_url', models.URLField(blank=True, max_length=2000)),
                ('insurance_id', models.UUIDField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'cymed_portal_invoices',
            },
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('invoice', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transactions',
                    to='cymed_portal_payments.patientinvoice',
                )),
                ('transaction_reference', models.CharField(db_index=True, max_length=255, unique=True)),
                ('cycom_transaction_id', models.CharField(blank=True, max_length=255)),
                ('payment_method', models.CharField(
                    choices=[
                        ('credit_card', 'Credit Card'),
                        ('debit_card', 'Debit Card'),
                        ('bank_transfer', 'Bank Transfer'),
                        ('digital_wallet', 'Digital Wallet'),
                        ('cash', 'Cash'),
                        ('insurance', 'Insurance'),
                        ('installment', 'Installment'),
                    ],
                    default='credit_card',
                    max_length=30,
                )),
                ('payment_gateway', models.CharField(blank=True, max_length=100)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('processing', 'Processing'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                        ('refunded', 'Refunded'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('gateway_response', models.JSONField(default=dict)),
                ('receipt_url', models.URLField(blank=True, max_length=2000)),
            ],
            options={
                'db_table': 'cymed_portal_payment_transactions',
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('method_type', models.CharField(
                    choices=[
                        ('credit_card', 'Credit Card'),
                        ('debit_card', 'Debit Card'),
                        ('bank_account', 'Bank Account'),
                        ('digital_wallet', 'Digital Wallet'),
                    ],
                    max_length=20,
                )),
                ('display_name', models.CharField(max_length=100)),
                ('last_four', models.CharField(blank=True, max_length=4)),
                ('card_brand', models.CharField(blank=True, max_length=30)),
                ('expiry_month', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('expiry_year', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('gateway_token', models.CharField(blank=True, max_length=500)),
            ],
            options={
                'db_table': 'cymed_portal_payment_methods',
            },
        ),
        migrations.CreateModel(
            name='InstallmentPlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('invoice', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='installment_plans',
                    to='cymed_portal_payments.patientinvoice',
                )),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('installment_count', models.PositiveSmallIntegerField()),
                ('installment_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('first_payment_date', models.DateField()),
                ('frequency', models.CharField(
                    choices=[
                        ('weekly', 'Weekly'),
                        ('biweekly', 'Biweekly'),
                        ('monthly', 'Monthly'),
                    ],
                    default='monthly',
                    max_length=10,
                )),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Active'),
                        ('completed', 'Completed'),
                        ('defaulted', 'Defaulted'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='active',
                    max_length=20,
                )),
                ('installments_paid', models.PositiveSmallIntegerField(default=0)),
                ('next_payment_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_installment_plans',
            },
        ),
        migrations.AddIndex(
            model_name='patientinvoice',
            index=models.Index(fields=['account_id', 'status', 'due_date'], name='cymed_portal_invoices_acct_status_due_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['account_id', 'status', 'paid_at'], name='cymed_portal_txn_acct_status_paid_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentmethod',
            index=models.Index(fields=['account_id', 'is_active'], name='cymed_portal_pm_acct_active_idx'),
        ),
        migrations.AddIndex(
            model_name='installmentplan',
            index=models.Index(fields=['account_id', 'status'], name='cymed_portal_inst_acct_status_idx'),
        ),
    ]
