# Implementation Data Model

This generated source summarizes verified data-ownership rules for assistant grounding.

- Customers own customer master and customer history truth.
- Planning owns orders, planning records, shifts, staffing, releases, and document packages linked to planning context.
- Platform services own centralized documents, document versions, document links, communications, notices, and integration jobs.
- Other modules may reference IDs and read projections, but they must not mutate another context's master truth directly.
- Contract-like content should be grounded as document ownership plus business context rather than as a fake standalone contract table or module.