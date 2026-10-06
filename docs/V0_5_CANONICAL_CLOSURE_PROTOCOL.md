# Prospective canonical physical-cache closure supplement

Primary 256-evaluation descent and a separate 128-evaluation completion are
preserved unchanged. Several one-round cat endpoints still admit later-round
reset removals. The design's omission tuples record edit order even though the
builder treats them as sets, creating multiple genome IDs for identical physical
circuits. This affects closure cost, not the validity of existing certificates.

Normalize only omitted-check, omitted-operation and omitted-terminal sets.
Preserve every order-sensitive field, including flag intervals, merged-record
order, interaction order, stabilizer basis and schedule choices. For every
imported record, rebuild the normalized design and require its full circuit hash
to equal the original saved circuit hash. Preserve original-to-canonical IDs.
Reuse conclusive VALID/INVALID/INVALID_STRUCTURE evidence only for an exactly
matching full circuit hash and target. Retry UNKNOWNs. This is proof reuse,
not an assumption that related circuits share distance.

Run one additional closure per primary replay: at most **1024 new canonical
design evaluations**, constrained by the remaining original 20000000 native
join-work allowance. This permits eight times the previous 128-evaluation phase
to complete several further reset-removal generations; it does not guarantee
minimality. Keep the same supported operators, eight-proposal batches, metrics,
certifier and ideal validator. Independently check final points and retain finite
remaining-edit lists for any unresolved case. Record physical cache hits,
aliases, ancestry and all limits. Save results separately under canonical_completion.

This supplement is specified before its runs and does not overwrite the primary
comparison or original completion. Report gains by phase. The public V0.5 CLI
uses the canonical closure with a configurable default 1024-evaluation limit;
earlier primary/completion source and results remain reproducible.
