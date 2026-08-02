# AGENTS.md

## Repository Contract

- `main` is the human-maintained control plane for workflows, scripts, tests, documentation, and the public signing key.
- `repo-state` is generated and updated only by GitHub Actions; do not edit its OSTree objects manually.
- GitHub Pages deploys the generated `repo-state` snapshot through the Actions Pages workflow.
- The application ref is always `app/io.github.vincentzyuapps.dartflutterdemo/x86_64/stable`.

## Security

- Never commit, print, upload, or cache the GPG private key or passphrase.
- Production signing material belongs only in the `flatpak-production` GitHub Environment.
- The armored public key and fingerprint are public and may be committed.
- Pin external publishing actions to reviewed commit SHAs.

## Validation

- Run `python -m unittest discover -s test -p "test_*.py"` after changing the renderer or workflow.
- Keep generated Flatpak descriptors parseable as GLib key files.
- A successful deployment must verify the public Pages repository with GPG enabled.
