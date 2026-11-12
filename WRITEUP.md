# Write-up

## What I focused on, and why

The solution is deterministic and offline. It prioritizes grounded predictions and valid evidence over generating a large number of speculative records. Open loops receive the largest labelled dev allocation (28 points), so extracting actionable requests and tracking clear responses was the first priority.

## My approach

- **Circles:** preserve seed labels; use explicit, referent-resolved kinship evidence and conservative chat-context cues. Unclear cases fall back to `friend`.
- **Organisations and chats:** use seed organisation names and clear title aliases to tie related chats together. Other groups are tied to an active participant rather than automatically becoming an organisation. Every input chat receives exactly one valid tie.
- **Open loops:** detect a narrow set of requests, actionable questions, and explicit commitments. Each source message is emitted at most once. Owners are inferred from the message direction and speaker. Status remains `open` unless the source or a relevant nearby reply gives clear completion or cancellation evidence; acknowledgements alone do not close a task.
- **Goals:** include a seeded goal only when a message provides matching evidence. Additional goals require explicit goal intent or a dated milestone/experience cue.
- The pipeline uses only the Python standard library and the existing `run.sh` interface.

## What it costs

No model or API is used: **$0 per 1,000 messages in API/model charges**. Runtime cost is local CPU and memory only; there are no tokens or network calls.

## Where it's wrong

On the labelled dev data, the official checker reports **21.1/56**: circles 4.4/12, organisations 1.8/8, chats 6.3/8, open loops found 5.1/14, and open loops closed right 3.4/14. Goals and help are not labelled in dev.

The loop detector emits 95 records and matches 31 gold sources: precision **32.6%**, recall **41.9%**, F1 **36.7%**. It still produces many false positives and misses terse or context-dependent gold events. Of the matched loops, 15 gold-open loops remain open, 13 gold-done loops are conservatively left open, and 3 gold-done loops are marked done. No matched gold-open loop is incorrectly closed.

Circle accuracy is **15/41** scored non-seed people. Titles and conversation cues are insufficient to reliably distinguish every family, staff, client, and colleague relationship. Organisation mapping also relies on visible names and aliases; unnamed or implicit organisational links remain weak. Dev answers provide no goal/help labels, so those components cannot be meaningfully calibrated here. Hidden-set performance is not known.
