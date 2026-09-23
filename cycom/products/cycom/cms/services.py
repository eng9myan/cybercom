from rest_framework.exceptions import ValidationError

from products.cycom.cms.models import CONTAINER_BLOCK_TYPES, PageBlock


def build_block_tree(page):
    """Flat block rows -> nested list, root blocks (parent=None) first,
    each with its own `children` list. One level deep by construction
    (CONTAINER_BLOCK_TYPES enforcement in reorder_blocks/serializer keeps a
    child from ever being a container itself), but this walk doesn't
    assume that — it'll nest however deep the data actually goes."""
    blocks = list(page.blocks.all())
    by_parent = {}
    for b in blocks:
        by_parent.setdefault(b.parent_id, []).append(b)

    def node(b):
        return {
            "id": str(b.id),
            "block_type": b.block_type,
            "order": b.order,
            "config": b.config,
            "children": [node(c) for c in by_parent.get(b.id, [])],
        }

    return [node(b) for b in by_parent.get(None, [])]


def reorder_blocks(page, moves, tenant_id):
    """Apply a batch of {id, parent, order} moves from a canvas drag.
    Every block referenced must belong to this page/tenant, and a
    container (section/columns) can never itself be nested inside
    another block -- both checked before anything is written, so a
    partial/invalid batch never applies half its moves."""
    block_ids = [m["id"] for m in moves]
    blocks_by_id = {
        str(b.id): b for b in PageBlock.objects.filter(id__in=block_ids, page=page, tenant_id=tenant_id)
    }
    if len(blocks_by_id) != len(block_ids):
        raise ValidationError("One or more blocks were not found on this page.")

    for move in moves:
        block = blocks_by_id[move["id"]]
        parent_id = move.get("parent")
        if parent_id:
            parent = blocks_by_id.get(parent_id) or PageBlock.objects.filter(
                id=parent_id, page=page, tenant_id=tenant_id
            ).first()
            if parent is None:
                raise ValidationError(f"Parent block {parent_id} not found on this page.")
            if parent.block_type not in CONTAINER_BLOCK_TYPES:
                raise ValidationError(f"Block type '{parent.block_type}' cannot contain child blocks.")
            if block.block_type in CONTAINER_BLOCK_TYPES:
                raise ValidationError("A section/columns block cannot be nested inside another block.")

    for move in moves:
        block = blocks_by_id[move["id"]]
        block.parent_id = move.get("parent") or None
        block.order = move["order"]
        block.save(update_fields=["parent", "order", "updated_at"])
