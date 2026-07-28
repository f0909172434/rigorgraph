# Beta release policy

RigorGraph is maintained by one person with AI assistance. Beta releases are governed by reproducible product evidence, not by waiting for a volunteer panel.

## Release gates

A beta may ship when all applicable deterministic gates pass:

- tests, lint, generated schemas, locale parity, plugin metadata, and the full release check;
- the offline viewer builds from source and contains no runtime network dependency;
- the wheel builds and installs cleanly in an isolated environment;
- supported demos complete and preserve the distinction between workflow verification and truth;
- the GitHub Action and documented quick start have no known release-blocking error.

An unresolved security defect, data-loss risk, invalid state transition, missing core translation, broken package, or broken documented golden path blocks the release.

## External evidence

External use is evidence, not permission. Feedback, fresh-install reports, and real repositories improve confidence and guide priorities, but no fixed number of testers is required before development or beta releases continue.

After each beta, maintainers track public and voluntarily reported signals such as:

- time to the first readable report;
- distinct external repositories using RigorGraph;
- confusing onboarding steps and reproducible failures;
- issues, contributions, and cases where an audit result was misleading.

RigorGraph does not add telemetry to obtain these signals. Private research data must not be submitted to public feedback forms.

## Solo-maintainer decision rule

Ship small, reversible improvements when the hard gates pass. If external adoption remains low, improve positioning, installation, demos, and onboarding before expanding product scope. Human approval remains required for publishing to package or marketplace accounts and for public social posts.
