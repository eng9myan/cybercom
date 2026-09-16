from rest_framework import serializers

from products.cyed.sif.models import SifRefId


class SifRefIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = SifRefId
        fields = "__all__"
        # Every field is read-only. A RefId is minted as a side effect of
        # emitting an object; letting one be edited afterwards would break the
        # single promise a RefId makes — that it never changes.
        read_only_fields = [f.name for f in SifRefId._meta.fields]
