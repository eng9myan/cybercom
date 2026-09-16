"""
import_mrac — load the real ACARA v9 Machine-Readable Australian Curriculum.

The MRAC vocabularies are published as SKOS/ASN JSON-LD on ACARA's PoolParty
server. Normal operation is OFFLINE: download the files once (or use --download),
then point this command at the directory.

    # one file
    python manage.py import_mrac --tenant <uuid> --file ./mrac/LA_MAT.jsonld --set LA/MAT

    # a whole directory (GC/CCP files are processed first, then learning areas)
    python manage.py import_mrac --tenant <uuid> --dir ./mrac

    # fetch from ACARA first (explicit opt-in; the only code path that hits the network)
    python manage.py import_mrac --tenant <uuid> --dir ./mrac --download
    python manage.py import_mrac --tenant <uuid> --dir ./mrac --download --sets LA/MAT,GC/N

    # see what would be parsed without writing anything
    python manage.py import_mrac --tenant <uuid> --file ./mrac/LA_MAT.jsonld --dry-run

Idempotent: re-running updates existing statements (matched on
tenant + code + framework) and never duplicates them.

The Australian Curriculum is CC BY 4.0; the ACARA attribution notice is printed
after every run and stored on the MracImportRun row.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from products.cyed.curriculum import mrac

DEFAULT_TENANT = "11111111-1111-1111-1111-111111111111"


class Command(BaseCommand):
    help = "Import ACARA v9 MRAC vocabularies (JSON-LD) for a tenant from a local file or directory."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default=DEFAULT_TENANT)
        parser.add_argument("--file", default=None, help="One MRAC JSON-LD export.")
        parser.add_argument("--dir", default=None, help="Directory of MRAC JSON-LD exports.")
        parser.add_argument("--set", dest="set_code", default=None,
                            help='Vocabulary set for --file, e.g. "LA/MAT" (inferred if omitted).')
        parser.add_argument("--framework", default="ACARA v9")
        parser.add_argument("--pattern", default="*.jsonld", help="Glob used with --dir.")
        parser.add_argument("--download", action="store_true",
                            help="Fetch the sets from vocabulary.curriculum.edu.au into --dir first.")
        parser.add_argument("--sets", default=None,
                            help="Comma-separated sets to download (default: all 18).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Parse and report counts without writing to the database.")

    def handle(self, *args, **options):
        target_dir = Path(options["dir"]) if options["dir"] else None
        target_file = Path(options["file"]) if options["file"] else None

        if options["download"]:
            if target_dir is None:
                raise CommandError("--download requires --dir (where to save the files).")
            sets = [s.strip() for s in (options["sets"] or ",".join(mrac.ALL_SETS)).split(",") if s.strip()]
            for set_code in sets:
                self.stdout.write(f"  fetching {set_code} → {mrac.mrac_url(set_code)}")
                try:
                    saved = mrac.download_set(set_code, target_dir, allow_network=True)
                except Exception as exc:  # network/404 must not abort the rest
                    self.stdout.write(self.style.WARNING(f"    failed: {exc}"))
                    continue
                self.stdout.write(self.style.SUCCESS(f"    saved {saved.name}"))

        if not target_dir and not target_file:
            raise CommandError("Provide --file or --dir.")

        if options["dry_run"]:
            self._dry_run(target_file, target_dir, options)
            return

        tenant = options["tenant"]
        if target_file:
            if not target_file.exists():
                raise CommandError(f"MRAC file not found: {target_file}")
            result = mrac.load_mrac(
                tenant, target_file, set_code=options["set_code"], framework=options["framework"]
            )
            self._report([result])
        else:
            if not target_dir.is_dir():
                raise CommandError(f"Not a directory: {target_dir}")
            bundle = mrac.load_mrac_directory(
                tenant, target_dir, framework=options["framework"], pattern=options["pattern"]
            )
            self._report(bundle["files"], totals=bundle["totals"])

        self.stdout.write("")
        self.stdout.write(self.style.WARNING(mrac.ACARA_ATTRIBUTION))

    # ── helpers ─────────────────────────────────────────────────────────────
    def _dry_run(self, target_file, target_dir, options):
        paths = [target_file] if target_file else sorted(Path(target_dir).rglob(options["pattern"]))
        for path in paths:
            if not path.exists():
                raise CommandError(f"MRAC file not found: {path}")
            kinds: dict[str, int] = {}
            for record in mrac.parse_mrac(
                path, set_code=options["set_code"], framework=options["framework"]
            ):
                kinds[record["kind"]] = kinds.get(record["kind"], 0) + 1
            detail = ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())) or "nothing parsed"
            self.stdout.write(f"  {path.name}: {detail}")
        self.stdout.write(self.style.SUCCESS("Dry run complete — nothing written."))
        self.stdout.write(self.style.WARNING(mrac.ACARA_ATTRIBUTION))

    def _report(self, results, totals=None):
        for result in results:
            self.stdout.write(
                f"  {result['source']} [{result['set_code'] or '?'}]: "
                f"{result['outcomes_created']} created, {result['outcomes_updated']} updated, "
                f"{result['elaborations_linked']} elaborations linked, "
                f"{result['standards_upserted']} achievement standards, "
                f"{result['capability_links']} GC links, {result['priority_links']} CCP links, "
                f"{result['skipped']} skipped"
            )
        if totals:
            self.stdout.write(self.style.SUCCESS(
                f"TOTAL: {totals['outcomes_created']} created, {totals['outcomes_updated']} updated, "
                f"{totals['statements_seen']} statements seen across {len(results)} file(s)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS("MRAC import complete."))
