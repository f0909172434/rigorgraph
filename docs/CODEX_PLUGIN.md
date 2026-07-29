# Codex plugin installation

Download `rigorgraph-codex-plugin-1.0.0-rc.2.zip` from the matching GitHub Release and extract it to a stable local directory. The bundle contains its own `rigorgraph-release` marketplace and does not edit the personal marketplace.

```console
codex plugin marketplace add PATH_TO_EXTRACTED_BUNDLE
codex plugin add rigorgraph@rigorgraph-release
codex plugin list
```

The installed plugin must report version `1.0.0-rc.2` and expose `research-intake`, `capture-claim`, `adversarial-verify`, and `release-audit`. Start a new Codex task before invoking those skills because an existing task does not reload newly installed plugin content.

To remove this release marketplace:

```console
codex plugin remove rigorgraph@rigorgraph-release
codex plugin marketplace remove rigorgraph-release
```

The plugin declares only skills. It has no MCP server, app, hook, telemetry, authentication flow, or paid model integration.
