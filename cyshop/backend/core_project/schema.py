import graphene
from graphene_django import DjangoObjectType
from apps.tenants.models import Tenant, Company, Branch
from apps.identity.models import User
from apps.notifications.models import SystemNotification
from apps.sales.models import Lead, Opportunity, Quotation, QuotationLine

class TenantType(DjangoObjectType):
    class Meta:
        model = Tenant
        fields = ("id", "name", "subdomain", "created_at")

class CompanyType(DjangoObjectType):
    class Meta:
        model = Company
        fields = ("id", "name", "country_code", "created_at")

class BranchType(DjangoObjectType):
    class Meta:
        model = Branch
        fields = ("id", "name", "address", "created_at")

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "created_at")

class NotificationType(DjangoObjectType):
    class Meta:
        model = SystemNotification
        fields = ("id", "title", "message", "notification_type", "is_read", "created_at")

# --- CRM & Sales Types ---
class LeadType(DjangoObjectType):
    class Meta:
        model = Lead
        fields = ("id", "name", "company", "contact_person", "email", "phone", "source", "status", "priority", "expected_revenue", "owner")

class OpportunityType(DjangoObjectType):
    class Meta:
        model = Opportunity
        fields = ("id", "lead", "name", "stage", "probability", "expected_revenue", "close_date", "owner")

class QuotationLineType(DjangoObjectType):
    class Meta:
        model = QuotationLine
        fields = ("id", "item_name", "qty", "unit_price", "discount", "line_total")

class QuotationType(DjangoObjectType):
    lines = graphene.List(QuotationLineType)

    class Meta:
        model = Quotation
        fields = ("id", "quotation_number", "company", "branch", "customer_name", "customer_type", "status", "discount_type", "discount_value", "tax_rate", "total_amount", "expiration_date")

    def resolve_lines(self, info):
        return self.lines.all()

class Query(graphene.ObjectType):
    all_tenants = graphene.List(TenantType)
    all_companies = graphene.List(CompanyType)
    all_branches = graphene.List(BranchType)
    all_users = graphene.List(UserType)
    my_notifications = graphene.List(NotificationType)
    
    # CRM & Sales Queries
    my_leads = graphene.List(LeadType)
    my_opportunities = graphene.List(OpportunityType)
    my_quotations = graphene.List(QuotationType)

    def resolve_all_tenants(self, info):
        return Tenant.objects.all()

    def resolve_all_companies(self, info):
        tenant_id = getattr(info.context, 'tenant_id', None)
        if tenant_id:
            return Company.objects.filter(tenant_id=tenant_id)
        return Company.objects.all()

    def resolve_all_branches(self, info):
        tenant_id = getattr(info.context, 'tenant_id', None)
        if tenant_id:
            return Branch.objects.filter(tenant_id=tenant_id)
        return Branch.objects.all()

    def resolve_all_users(self, info):
        tenant_id = getattr(info.context, 'tenant_id', None)
        if tenant_id:
            return User.objects.filter(tenant_id=tenant_id)
        return User.objects.all()

    def resolve_my_notifications(self, info):
        if info.context.user.is_authenticated:
            return SystemNotification.objects.filter(user=info.context.user, tenant_id=info.context.tenant_id)
        return []

    def resolve_my_leads(self, info):
        tenant_id = getattr(info.context, 'tenant_id', None)
        if info.context.user.is_authenticated and tenant_id:
            return Lead.objects.filter(tenant_id=tenant_id, owner=info.context.user)
        return []

    def resolve_my_opportunities(self, info):
        tenant_id = getattr(info.context, 'tenant_id', None)
        if info.context.user.is_authenticated and tenant_id:
            return Opportunity.objects.filter(tenant_id=tenant_id, owner=info.context.user)
        return []

    def resolve_my_quotations(self, info):
        tenant_id = getattr(info.context, 'tenant_id', None)
        if tenant_id:
            return Quotation.objects.filter(tenant_id=tenant_id)
        return []

class CreateTenant(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        subdomain = graphene.String(required=True)

    tenant = graphene.Field(TenantType)

    def mutate(self, info, name, subdomain):
        tenant = Tenant.objects.create(name=name, subdomain=subdomain)
        return CreateTenant(tenant=tenant)

class MarkNotificationRead(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        if info.context.user.is_authenticated:
            try:
                notification = SystemNotification.objects.get(id=id, user=info.context.user)
                notification.is_read = True
                notification.save()
                return MarkNotificationRead(success=True)
            except SystemNotification.DoesNotExist:
                return MarkNotificationRead(success=False)
        return MarkNotificationRead(success=False)

# --- CRM & Sales Mutations ---
class CreateLead(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        expected_revenue = graphene.Float()

    lead = graphene.Field(LeadType)

    def mutate(self, info, name, email, expected_revenue=0.0):
        if info.context.user.is_authenticated:
            tenant_id = getattr(info.context, 'tenant_id', None)
            lead = Lead.objects.create(
                tenant_id=tenant_id,
                name=name,
                email=email,
                expected_revenue=expected_revenue,
                owner=info.context.user
            )
            return CreateLead(lead=lead)
        return CreateLead(lead=None)

class ConvertLead(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    success = graphene.Boolean()
    opportunity_id = graphene.UUID()

    def mutate(self, info, id):
        if info.context.user.is_authenticated:
            try:
                lead = Lead.objects.get(id=id, tenant_id=info.context.tenant_id)
                if lead.status == 'QUALIFIED':
                    return ConvertLead(success=False, opportunity_id=None)

                lead.status = 'QUALIFIED'
                lead.save()

                opp_name = f"Opp - {lead.company if lead.company else lead.name}"
                opp = Opportunity.objects.create(
                    tenant_id=info.context.tenant_id,
                    lead=lead,
                    name=opp_name,
                    stage='QUALIFIED',
                    probability=20,
                    expected_revenue=lead.expected_revenue,
                    owner=lead.owner
                )
                return ConvertLead(success=True, opportunity_id=opp.id)
            except Lead.DoesNotExist:
                return ConvertLead(success=False, opportunity_id=None)
        return ConvertLead(success=False, opportunity_id=None)

class Mutation(graphene.ObjectType):
    create_tenant = CreateTenant.Field()
    mark_notification_read = MarkNotificationRead.Field()
    
    # CRM & Sales
    create_lead = CreateLead.Field()
    convert_lead = ConvertLead.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
