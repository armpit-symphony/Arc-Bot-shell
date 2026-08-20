# Governed document listing

Status: bounded physical-PC test capability. Not production-ready.

Arc exposes document_list only through the same signed operator request,
Supervisor classification, Guardian decision, LIMA single-use execution grant,
and Arc-local execution opt-in used by document_read. The corresponding
operator action is safe_list.

## Result contract

A successful request returns a non-recursive projection of one directory under
the configured document root:

- at most 200 entries;
- deterministic case-insensitive name ordering;
- base name and root-relative path only;
- file or directory kind;
- byte size for regular files and null for directories;
- an explicit truncated flag.

The projection excludes hidden names, symlinks, special files, content,
timestamps, owners, permissions, and absolute paths. Names containing Unicode
control or format characters are also excluded.

The root directory is addressed as a single dot. Nested directories use
slash-separated relative paths. Absolute paths, drive-qualified paths, parent
traversal, and hidden directory segments are denied after Arc independently
resolves and checks containment.

## Authority boundary

A Supervisor grant is necessary but not sufficient. Arc acts only when all of
these hold:

1. Supervisor execution opt-in was enabled at startup.
2. Arc execution opt-in was enabled at startup.
3. A document root was explicitly configured.
4. The grant is current, single-use, side-effect-free, and bound to the exact
   tenant, worker, request, safe_list action, and document_list capability.
5. The requested directory remains inside the resolved document root.

No listing code can read content, mutate storage, send data, open a connector,
or perform network egress.

LIMA Office independently validates the returned shape and reconstructs every
relative path from the requested directory plus the returned base name. A
malformed Arc result is routed as arc_listing_malformed, exposes no entries,
and fails closed. Durable IDE evidence stores counts and reason codes, not the
listed names.
