# Contributing to Multi-PLC Water Treatment Testbed

Thank you for your interest in the Multi-PLC Water Treatment Testbed. This document sets out how the project handles contributions during its current phase, and what to expect once it opens up for wider collaboration.

---

## Current phase: controlled research artefact

The Multi-PLC Water Treatment Testbed is currently a research artefact associated with doctoral research at Keele University. The project is being developed to support evaluation of agentic and generative AI approaches for autonomous vulnerability assessment and penetration testing in OT/ICS environments.

During this phase, external contributions may be limited or declined where they could affect the reproducibility, integrity, or novelty of the research.

This may apply to:

- Pull requests
- Issues opened by people outside the maintainer's research group
- Discussions, comments, and reviews from the wider community
- Changes that alter the seeded vulnerabilities, architecture, or evaluation assumptions

If you have access to this repository before public release and were not invited as a collaborator or named research contributor, please treat the contents as confidential and contact the maintainer at **[s.r.a.truss@keele.ac.uk](mailto:s.r.a.truss@keele.ac.uk)**.

This contribution posture may change once the related research has been published and the repository is maintained as a public research artefact.

---

## Contribution model

Once the repository is open for wider contribution, contributions will be welcomed under the terms below. Do not assume unrestricted contribution is in force until this notice has been updated.

### Before you contribute

1. **Read the research ethics statement** in [`docs/ethics.md`](docs/ethics.md), if present. All contributions must be consistent with the intended research use of the testbed.
2. **Read the security policy** in [`SECURITY.md`](SECURITY.md). Security issues must not be filed as public issues or pull requests.
3. **Search existing issues and discussions** to see whether your idea or bug report already exists.
4. **For non-trivial changes, open an issue first** using the appropriate template to discuss the proposed direction before writing code. This avoids wasted effort on changes that may not fit the research design.

---

## What kinds of contribution are welcome

- Bug fixes with reproducible test cases.
- Documentation improvements, including clearer setup instructions, architecture descriptions, diagrams, and examples.
- Improvements to Docker configuration, reproducibility, or developer experience.
- Test coverage for PLC behaviour, network segmentation, HMI access, and seeded vulnerabilities.
- New simulation components that improve the realism of the water-treatment process without breaking existing assumptions.
- Improvements to the evaluation harness, telemetry, logging, or evidence collection.
- Research collaborations, ablations, and experiments. Please open a `Research question / experiment proposal` issue before opening a pull request.

---

## What will be declined

The following contributions will usually be declined:

- Changes whose primary effect is to weaken, bypass, or remove safety, scope, or policy controls.
- Changes that make the testbed target real-world systems by default.
- Code or configurations that include hardcoded targeting of any non-lab environment.
- Contributions that introduce live offensive capability outside the contained testbed.
- Changes that alter seeded vulnerabilities without documenting the research rationale.
- Material that includes credentials, target-identifying information, engagement data, or other sensitive content.
- Drive-by reformatting, mass renames, or stylistic-only changes that do not address an issue.
- Changes that reduce reproducibility by using unpinned images, floating dependencies, or undocumented manual steps.

The maintainer reserves the right to decline any contribution at their discretion, including for reasons not listed here. Decline reasons will be given in good faith.

---

## Development workflow

1. **Fork the repository** and create a feature branch from `main`.
2. **Make your changes** in small, logically coherent commits with clear messages.
3. **Add or update tests** under `tests/`. New behaviour without tests may be sent back.
4. **Update documentation** under `docs/` and `README.md` where the change affects user-visible behaviour.
5. **Run the local checks** before opening the pull request.
6. **Open a pull request** against `main` using the PR template. Fill in every section.
7. **Respond to review feedback.** Pull requests that go silent for an extended period may be closed and reopened when ready.

---

## Local checks

The repository uses standard Python and Docker-based tooling. Run the relevant checks locally before submitting:

```bash
pytest
ruff check .
ruff format --check .
mypy .
