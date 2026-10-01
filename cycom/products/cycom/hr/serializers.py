from rest_framework import serializers

from products.cycom.hr.models import Contract, Department, Employee, EmployeeDocument, EmployeeInsurance


class EmployeeSerializer(serializers.ModelSerializer):
    # email / phone are EncryptedText (BinaryField storage); DRF would otherwise
    # base64-encode them. The field hands us plain text on read / write.
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=50)

    class Meta:
        model = Employee
        fields = [
            "id", "tenant_id", "employee_number", "first_name", "last_name",
            "email", "phone", "job_title", "department", "department_unit", "hire_date", "status",
            "marital", "spouse_employed", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ContractSerializer(serializers.ModelSerializer):
    hourly_rate = serializers.DecimalField(max_digits=12, decimal_places=4, read_only=True)

    class Meta:
        model = Contract
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDocument
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class EmployeeInsuranceSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeInsurance
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class DepartmentSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True, default=None)
    manager_name = serializers.SerializerMethodField()
    member_ids = serializers.SerializerMethodField()
    child_ids = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    total_employee = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "code", "parent", "parent_name", "manager", "manager_name", "is_active",
                  "member_ids", "child_ids", "member_count", "total_employee", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _tree(self):
        """{dept_id: (direct member ids, child ids)} for the tenant, built
        once per request (the list view passes it in context)."""
        tree = self.context.get("department_tree")
        if tree is None:
            tree = build_department_tree(self.instance.tenant_id if isinstance(self.instance, Department)
                                         else self.context["request"].tenant_id)
            self.context["department_tree"] = tree
        return tree

    def get_manager_name(self, obj):
        m = obj.manager
        return f"{m.first_name} {m.last_name}".strip() if m else None

    def get_member_ids(self, obj):
        return [str(i) for i in self._tree().get(obj.pk, ([], []))[0]]

    def get_child_ids(self, obj):
        return [str(i) for i in self._tree().get(obj.pk, ([], []))[1]]

    def get_member_count(self, obj):
        return len(self._tree().get(obj.pk, ([], []))[0])

    def get_total_employee(self, obj):
        tree, total, stack, seen = self._tree(), 0, [obj.pk], set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            members, children = tree.get(node, ([], []))
            total += len(members)
            stack.extend(children)
        return total

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        if parent is not None and self.instance is not None:
            if parent.pk == self.instance.pk or parent.pk in self.instance.descendant_ids():
                raise serializers.ValidationError({"parent": "A department can't sit under itself or its own sub-department."})
        return attrs


def build_department_tree(tenant_id) -> dict:
    tree: dict = {}
    for pk, parent_id in Department.objects.filter(tenant_id=tenant_id).values_list("pk", "parent_id"):
        tree.setdefault(pk, ([], []))
        if parent_id:
            tree.setdefault(parent_id, ([], []))[1].append(pk)
    for emp_id, dept_id in Employee.objects.filter(tenant_id=tenant_id, department_unit__isnull=False)             .exclude(status="terminated").values_list("pk", "department_unit_id"):
        tree.setdefault(dept_id, ([], []))[0].append(emp_id)
    return tree
