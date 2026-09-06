from rest_framework import serializers
from .models import Account, Journal, JournalEntry, JournalEntryLine, FiscalPeriod


class AccountSerializer(serializers.ModelSerializer):
    parent_code = serializers.CharField(source='parent.code', read_only=True, allow_null=True)

    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    debit = serializers.DecimalField(max_digits=15, decimal_places=2,
                                     min_value=0, required=False, default=0)
    credit = serializers.DecimalField(max_digits=15, decimal_places=2,
                                      min_value=0, required=False, default=0)

    class Meta:
        model = JournalEntryLine
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        d, c = data.get('debit') or 0, data.get('credit') or 0
        if d and c:
            raise serializers.ValidationError('A line is a debit or a credit, not both.')
        if not d and not c:
            raise serializers.ValidationError('A line needs a debit or a credit amount.')
        return data

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)


class _EntryLineInput(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    description = serializers.CharField(required=False, allow_blank=True, default='')
    debit = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0, default=0)
    credit = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0, default=0)
    line_order = serializers.IntegerField(required=False, default=0)

    def validate(self, data):
        d, c = data.get('debit') or 0, data.get('credit') or 0
        if d and c:
            raise serializers.ValidationError('A line is a debit or a credit, not both.')
        if not d and not c:
            raise serializers.ValidationError('A line needs a debit or a credit amount.')
        return data


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True, read_only=True)
    lines_input = _EntryLineInput(many=True, write_only=True, required=False)
    journal_name = serializers.CharField(source='journal.name', read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)

    class Meta:
        model = JournalEntry
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _guard_posted(self, status_value, lines):
        if status_value != 'posted':
            return
        tot_d = sum((ln.get('debit') or 0) for ln in lines)
        tot_c = sum((ln.get('credit') or 0) for ln in lines)
        if not lines or tot_d != tot_c:
            raise serializers.ValidationError(
                {'status': 'Cannot save as posted: the entry must have lines and '
                           'total debits must equal total credits. Add lines first, '
                           'then call post_entry.'})

    def create(self, validated_data):
        lines = validated_data.pop('lines_input', [])
        self._guard_posted(validated_data.get('status'), lines)
        validated_data['tenant_id'] = self.context['request'].tenant_id
        entry = super().create(validated_data)
        self._write_lines(entry, lines)
        return entry

    def update(self, instance, validated_data):
        lines = validated_data.pop('lines_input', None)
        check = lines if lines is not None else list(
            instance.lines.filter(is_deleted=False).values('debit', 'credit'))
        self._guard_posted(validated_data.get('status', instance.status), check)
        entry = super().update(instance, validated_data)
        if lines is not None:
            entry.lines.all().delete()
            self._write_lines(entry, lines)
        return entry

    def _write_lines(self, entry, lines):
        for i, ln in enumerate(lines):
            JournalEntryLine.objects.create(
                entry=entry, tenant_id=entry.tenant_id,
                line_order=ln.get('line_order') or i,
                account=ln['account'], description=ln.get('description', ''),
                debit=ln.get('debit') or 0, credit=ln.get('credit') or 0)


class FiscalPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalPeriod
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['tenant_id'] = self.context['request'].tenant_id
        return super().create(validated_data)

    def validate(self, data):
        start = data.get('start_date') or (self.instance.start_date if self.instance else None)
        end = data.get('end_date') or (self.instance.end_date if self.instance else None)
        if start and end and start >= end:
            raise serializers.ValidationError({'end_date': 'end_date must be after start_date.'})
        return data
