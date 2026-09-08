# V2 Engineering Lifecycle

This compact global authority defines the default V2 construction and
deployment lifecycle. It is not a child of Data Truth or any other domain
responsibility.

```text
Responsibility ownership
→ Contract / Interface
→ Leaf implementation
→ Adapter
→ Composition
→ Integration Test
→ Runtime deployment
→ Canonical activation
```

1. Establish responsibility and tree ownership before implementation.
2. Use stable interfaces and adapters at cross-responsibility, external API,
   database, or runtime seams when replacement or isolation has real value.
   Pure internal semantic logic does not require artificial interfaces.
3. Lower-level implementations adapt to approved upper contracts; do not
   reshape the upper architecture around one database or vendor API. Prefer
   mature upstream mechanics behind adapters.
4. Compose and wire bounded leaves only after they satisfy their contracts.
5. Deploy runtime capability only after implementation and integration
   validation. Canonical or production activation is last and separately
   authorized when required.
6. Infrastructure installed or exercised earlier for upstream-fit work or a
   bounded POC is capability evidence, not business-contract authority.
7. Do not create an interface per function or a module per message family.

## Independent review visibility

Local implementation remains allowed. Codex or another local execution agent
may implement in the local repository, run local tests, inspect local diffs,
perform local self-review, and prepare a bounded candidate. GitHub publication
is required only at the formal ChatGPT independent implementation or
architecture review boundary, not for every intermediate local edit.

ChatGPT does not directly access the user's local worktree. When a candidate
exists only locally, ChatGPT may assess a Codex report, reported test results,
reported Git state, and reported local audit findings; that assessment is not
ChatGPT independent code review, direct code audit, or independent
implementation review because the actual candidate source was not inspected.
A local agent reviewing its own work remains local/self-review evidence.

Before formal ChatGPT independent implementation or architecture review:

1. publish the candidate branch to GitHub;
2. open a Draft PR with the intended base SHA preserved; and
3. expose the actual candidate source and tests remotely.

The formal review inspects the GitHub-visible PR metadata, base and head SHAs,
changed files, actual source and tests, commit history, relevant
architecture/status documentation, and Hosted CI as applicable. Its result is
bound to the exact reviewed GitHub head SHA.

A Draft PR is a review surface only. Publishing it does not mean
implementation PASS, review PASS, approval to merge, runtime authorization, or
production authorization. Merge remains separately guarded and authorized.

When ChatGPT finds defects, prefer normal bounded fix commits on the same PR
branch. The PR then updates and ChatGPT remotely re-audits the new exact head.
Do not amend, rebase, or force-push merely to make review history look cleaner;
preserve audit/fix ancestry unless separately authorized otherwise.

If source, tests, contracts, or materially relevant authority documentation
changes after the reviewed head, the previous formal review PASS does not cover
the new head; the changed scope requires remote re-audit. Pure PR metadata or
separately bounded status-only changes may receive bounded remote verification
without unnecessarily reopening the entire implementation review.

Hosted CI PASS does not substitute for independent review PASS, and Codex local
review PASS does not substitute for ChatGPT independent review PASS. They are
separate evidence inputs with different ownership. If a candidate cannot be
made visible on GitHub, ChatGPT must not claim to have independently audited
the actual code; the workflow remains pending independent remote review.

The normal formal flow, when ChatGPT independent code or architecture review is
required, is:

```text
Local implementation
→ local validation / local self-review
→ publish candidate branch
→ GitHub Draft PR
→ ChatGPT direct remote code audit
→ bounded fixes on same PR when required
→ ChatGPT remote re-audit of exact head
→ exact-head Hosted CI
→ guarded merge
→ post-merge validation / seal as required
```
