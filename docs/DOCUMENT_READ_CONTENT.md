# Returning document content

Reading a document and showing it are two different acts. The grant authorizes
the read; showing the text is something the operator asks for on top of it.
Arc keeps them separate.

## Why a separate opt-in

Until now a granted `document_read` returned a byte count and identifiers and
nothing else. That proved the governed path worked end to end, but it meant no
office task could actually complete, because there was nothing for an operator
to read.

Returning content is strictly more sensitive than counting bytes, so it gets
its own flag rather than riding along with the existing one:

```bash
arc-preflight ... \
  --execute-granted-capability \
  --document-root /path/to/documents \
  --emit-document-content
```

All three are still required, and each defaults off. `--emit-document-content`
is **not** a way around the other two — without a valid grant, without Arc's
execution opt-in, or without a configured document root, it yields nothing.

## Content never travels inside the result

The JSON result stays free of document content, always, even when content is
being shown. Content is printed after it, in a delimited block:

```
{
  "execution": { "performed": true, "byte_count": 33, "content_emitted": true, ... }
}
--- BEGIN DOCUMENT CONTENT 'report.txt' (33 bytes) ---
Q3 revenue summary.
Second line.
--- END DOCUMENT CONTENT ---
```

That split is deliberate. The result is the part that gets piped, logged, and
kept; a document that leaked into it would end up in places nobody decided to
put it. So anything consuming this command by machine should simply not pass
`--emit-document-content`, and with the flag off the output remains pure JSON.

The execution record reports what happened:

| Field | Meaning |
|---|---|
| `content_emitted` | Whether text was shown |
| `content_reason_code` | Why it was not, when it was not |

`content_reason_code` is `content_not_requested` when the read succeeded and
the operator simply did not ask to see it.

## Arc still performs no writes

There is deliberately no `--content-output FILE` flag. Writing a file is a side
effect, and the grant asserts `side_effects_allowed: false`; Arc reporting
`side_effects_performed: false` while having written a file would be false.

Redirect the output yourself if you want it on disk. That write belongs to your
shell, not to Arc.

## Non-text documents

Content is decoded as UTF-8 strictly. A file that does not decode is still read
and still counted, but its text is withheld with
`content_reason_code: document_not_utf8_text`.

The alternative — decoding with replacement characters — would hand the
operator plausible looking text that is not what the file says. For a system
whose whole point is that you can trust what it tells you, a lossy read is
worse than a refusal.

## Limits

- Reads remain capped at 1 MB (`MAX_DOCUMENT_BYTES`).
- Path containment is resolved before the check, so symlinks and `..` cannot
  escape `--document-root`.
- `document_read` remains the only honoured capability. Anything that writes,
  sends, or deletes has no code path in Arc at all.
