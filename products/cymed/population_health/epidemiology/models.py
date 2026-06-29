from django.db import models

from platform.common.models import BaseModel

STUDY_TYPE_CHOICES = [
    ("cohort", "Cohort"),
    ("case_control", "Case-Control"),
    ("cross_sectional", "Cross-Sectional"),
    ("rct", "Randomised Controlled Trial"),
    ("surveillance", "Surveillance"),
    ("registry", "Registry"),
    ("ecological", "Ecological"),
]

STUDY_STATUS_CHOICES = [
    ("planning", "Planning"),
    ("recruiting", "Recruiting"),
    ("active", "Active"),
    ("analysis", "Analysis"),
    ("completed", "Completed"),
    ("published", "Published"),
]

PERIOD_TYPE_CHOICES = [
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("quarterly", "Quarterly"),
    ("annual", "Annual"),
]

INDICATOR_TYPE_CHOICES = [
    ("health_outcome", "Health Outcome"),
    ("social_determinant", "Social Determinant"),
    ("health_system", "Health System"),
    ("demographic", "Demographic"),
    ("environmental", "Environmental"),
    ("economic", "Economic"),
]

GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
    ("all", "All"),
]

MEASURE_TYPE_CHOICES = [
    ("morbidity", "Morbidity"),
    ("mortality", "Mortality"),
    ("fertility", "Fertility"),
    ("disability", "Disability"),
    ("life_expectancy", "Life Expectancy"),
    ("daly", "DALY"),
    ("qaly", "QALY"),
    ("healthy_life_years", "Healthy Life Years"),
]


class EpidemiologyStudy(BaseModel):
    class Meta:
        app_label = "cymed_ph_epidemiology"
        db_table = "cymed_ph_epi_studies"

    study_name = models.CharField(max_length=200)
    study_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    study_type = models.CharField(max_length=30, choices=STUDY_TYPE_CHOICES)
    # ICD-11 code sourced from TerminologyService — no local term table
    disease_code = models.CharField(max_length=20, blank=True)
    disease_name = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    population_scope = models.CharField(max_length=200, blank=True)
    sample_size = models.PositiveIntegerField(null=True, blank=True)
    study_lead_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STUDY_STATUS_CHOICES, default="planning")
    objectives = models.TextField(blank=True)
    methodology = models.TextField(blank=True)
    fhir_research_study_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.study_name} ({self.study_type})"


class DiseaseTrend(BaseModel):
    class Meta:
        app_label = "cymed_ph_epidemiology"
        db_table = "cymed_ph_epi_disease_trends"
        unique_together = [
            ["tenant_id", "disease_code", "period_type", "period_date", "geographic_scope"]
        ]

    # ICD-11 code sourced from TerminologyService — no local term table
    disease_code = models.CharField(max_length=20)
    disease_name = models.CharField(max_length=200)
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPE_CHOICES)
    period_date = models.DateField()
    case_count = models.PositiveIntegerField(default=0)
    # Per 100,000 population
    incidence_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    prevalence_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    mortality_rate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    geographic_scope = models.CharField(max_length=200, blank=True)
    population_denominator = models.PositiveIntegerField(null=True, blank=True)
    data_source = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.disease_name} — {self.period_type} {self.period_date}"


class PopulationIndicator(BaseModel):
    class Meta:
        app_label = "cymed_ph_epidemiology"
        db_table = "cymed_ph_epi_indicators"

    indicator_code = models.CharField(max_length=50, unique=True)
    indicator_name = models.CharField(max_length=200)
    indicator_type = models.CharField(max_length=30, choices=INDICATOR_TYPE_CHOICES)
    value = models.DecimalField(max_digits=14, decimal_places=4)
    unit = models.CharField(max_length=50, blank=True)
    measurement_date = models.DateField()
    geographic_scope = models.CharField(max_length=200, blank=True)
    data_source = models.CharField(max_length=200, blank=True)
    age_group = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=GENDER_CHOICES)
    confidence_interval_low = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    confidence_interval_high = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )

    def __str__(self):
        return f"{self.indicator_code} — {self.indicator_name}"


class HealthMeasure(BaseModel):
    class Meta:
        app_label = "cymed_ph_epidemiology"
        db_table = "cymed_ph_epi_health_measures"

    measure_name = models.CharField(max_length=200)
    measure_type = models.CharField(max_length=30, choices=MEASURE_TYPE_CHOICES)
    value = models.DecimalField(max_digits=14, decimal_places=4)
    unit = models.CharField(max_length=50, blank=True)
    period_year = models.PositiveSmallIntegerField()
    geographic_scope = models.CharField(max_length=200, blank=True)
    age_group = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=10, blank=True, choices=GENDER_CHOICES)
    data_source = models.CharField(max_length=200, blank=True)
    # ICD-11 code from TerminologyService — for condition-specific measures
    icd11_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.measure_name} ({self.measure_type}, {self.period_year})"
