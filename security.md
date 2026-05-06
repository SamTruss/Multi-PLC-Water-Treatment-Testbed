# Security Policy

This document covers two distinct concerns:

1. **Vulnerabilities in the Multi-PLC Water Treatment Testbed itself** — bugs in this codebase, configuration, containers, documentation, or supporting scripts that could cause unintended exposure, unsafe behaviour, or data leakage.
2. **Vulnerabilities discovered using the testbed** — flaws in third-party software, services, libraries, or systems identified during authorised research or experimentation.

Both are taken seriously and handled under coordinated disclosure principles.

---

## 1. Reporting a vulnerability in the testbed

If you believe you have found a security issue in the Multi-PLC Water Treatment Testbed — for example, a flaw that causes unintended exposure outside the intended lab environment, weakens network isolation, leaks data, or creates unsafe behaviour not documented as part of the seeded research environment — please report it privately.

### Preferred channel

Email **[s.r.a.truss@keele.ac.uk](mailto:s.r.a.truss@keele.ac.uk)** with:

- A clear description of the issue and its impact.
- Reproduction steps, ideally minimal and self-contained.
- The commit hash, release, or branch against which you observed the behaviour.
- Any proof-of-concept code or artefacts, excluding third-party data, credentials, or material from systems you do not own.
- Your preferred name and affiliation for any acknowledgement, or a clear request to remain anonymous.

Please use the subject line prefix **`[Multi-PLC Testbed Security]`** so reports can be identified clearly.

---

## 2. What counts as a security issue

This repository intentionally contains vulnerable components and insecure configurations for controlled research. Not every weakness is a reportable security issue.

### In scope

The following are in scope for this policy:

- Bugs that expose the testbed outside its intended Docker/lab environment.
- Container, network, or firewall misconfigurations that break documented isolation assumptions.
- Documentation that, if followed exactly, would expose vulnerable services to public or unintended networks.
- Scripts or tooling that accidentally target systems outside the lab scope.
- Hardcoded real credentials, tokens, secrets, or private data.
- Supply-chain risks introduced by dependencies, base images, or unpinned artefacts.
- Behaviour that materially differs from the documented seeded vulnerabilities or expected lab behaviour.

### Out of scope

The following are generally out of scope:

- Seeded vulnerabilities intentionally included for research, such as deliberately exposed services, default credentials, weak segmentation assumptions, or intentionally vulnerable lab components.
- Findings that only affect the local lab instance when it is deployed as documented.
- Vulnerabilities in third-party tools, images, or platforms used by the testbed. These should be reported upstream to the relevant vendor or maintainer.
- Vulnerabilities in LLM providers, AI models, or external APIs connected by an operator. These should be reported to the relevant provider.
- Issues that require the operator to deliberately bypass documented safety guidance.
- Findings produced by running the testbed, agents, or scripts against systems without authorisation.

---

## 3. What to expect
<!--
This repository is a work-in-progress doctoral research artefact maintained alongside full-time employment and PhD write-up commitments. Security reports are appreciated and will be reviewed in good faith, but response times are not guaranteed.

Reports will be:

- Noted and retained for maintainer review.
- Prioritised according to severity, exploitability, and risk of unintended exposure.
- Addressed when practical within the constraints of the research schedule.
- Reflected in issues, documentation, commits, or release notes where appropriate.

For critical issues that create a realistic risk of unintended exposure, data leakage, or unsafe behaviour outside the intended lab environment, the maintainer will make reasonable efforts to prioritise review and mitigation.

This project does not currently operate a formal vulnerability disclosure programme, service-level agreement, or guaranteed remediation timeline.
-->
This repository is a work-in-progress doctoral research artefact maintained alongside full-time employment and PhD write-up commitments. Security reports are appreciated and will be reviewed in good faith, but response times are not guaranteed.

Reports will be:

- Noted and retained for maintainer review.
- Prioritised according to severity, exploitability, and risk of unintended exposure.
- Addressed when practical within the constraints of the research schedule.
- Reflected in issues, documentation, commits, or release notes where appropriate.

For critical issues that create a realistic risk of unintended exposure, data leakage, or unsafe behaviour outside the intended lab environment, the maintainer will make reasonable efforts to prioritise review and mitigation.

This project does not currently operate a formal vulnerability disclosure programme, service-level agreement, or guaranteed remediation timeline.

---

## 4. Safe harbour

Good-faith security research on the Multi-PLC Water Treatment Testbed, conducted against your own copy of the repository or against systems you own or are authorised to assess, is welcomed.

The maintainer will not pursue legal action against researchers who:

- Make a good-faith effort to avoid privacy violations, data destruction, and service disruption.
- Keep testing within systems they own or are explicitly authorised to assess.
- Report findings privately through the channel above before public disclosure.
- Do not use the research to access, modify, or exfiltrate data belonging to third parties.
- Do not use the testbed or associated tooling to target real-world systems without authorisation.

This safe harbour applies only to research on this repository and deployments you own or are authorised to test. It does **not** authorise testing of any other system.

---

## 5. Vulnerabilities discovered using the testbed

Because this repository supports OT/ICS security research, operators may identify previously unknown vulnerabilities in third-party software, libraries, services, or appliances while experimenting with components, agents, or evaluation workflows.

### Default expectation: coordinated disclosure

If the testbed, or tooling developed from it, identifies a previously unknown vulnerability in third-party software during authorised research, the operator is expected to follow coordinated disclosure with the affected vendor or maintainer.

The maintainer recommends:

- Reporting the finding privately to the vendor's published security contact, such as their own `SECURITY.md`, security mailing list, or vulnerability disclosure programme.
- Allowing a reasonable remediation window, typically **90 days** from acknowledged receipt, before public disclosure.
- Coordinating a CVE assignment where the vulnerability has third-party impact, via the relevant CNA or MITRE.
- Avoiding publication of exploit code, target-identifying details, or weaponised artefacts before remediation, except where strictly necessary for academic publication and where the vendor has had reasonable opportunity to remediate.

### Findings in owned or lab systems

Findings against systems the operator owns or controls, including deliberately vulnerable lab targets packaged with or deployed for the testbed, do not require external disclosure. They may be reported, archived, and published according to the operator's research plan, institutional approvals, and ethical constraints.

### Academic publication

Findings intended for academic publication should follow the disclosure expectations above and the policies of the target venue.

Where a venue requires anonymisation, redact target identifiers but retain enough technical detail for the work to be reproducible against equivalent lab setups.

### What this repository is not

The Multi-PLC Water Treatment Testbed is not a vulnerability disclosure programme for any third-party product.

Do not report third-party vulnerabilities to the testbed maintainer unless the vulnerability directly affects this repository, its packaged configuration, or its documented deployment assumptions. Report third-party vulnerabilities to the vendor or maintainer responsible for the affected software.

---

## 6. Unauthorised use is not a security finding

If a report describes findings produced by running the testbed, an agent, or any tool against systems for which the reporter does not hold explicit, written authorisation, the report may be:

- Closed without remediation.
- Logged for the maintainer's records.
- Reported to relevant authorities where the activity appears to constitute a criminal offence under the **Computer Misuse Act 1990** in the UK, the **Computer Fraud and Abuse Act** in the US, or equivalent legislation in the relevant jurisdiction.

The safe harbour in Section 4 does not cover unauthorised activity.

See the authorised-use statement in [`README.md`](README.md) and the full ethics policy in [`docs/ethics.md`](docs/ethics.md).

---

## 7. Handling seeded vulnerabilities

This repository may intentionally include vulnerable services, insecure defaults, weak configurations, or constrained exploit paths for research and evaluation.

Seeded vulnerabilities should be clearly documented in the README, relevant phase documentation, tests, and evaluation scripts where appropriate.

Please do not report documented seeded vulnerabilities as security issues unless:

- They behave outside the documented scope;
- They expose systems beyond the intended lab environment;
- They create unintended host, network, or supply-chain risk;
- They differ materially from the behaviour described in the documentation.

Reports that improve the documentation, containment, or reproducibility of seeded vulnerabilities are welcome.

---

## 8. Acknowledgements

Researchers who report valid vulnerabilities in the Multi-PLC Water Treatment Testbed under this policy will be acknowledged in release notes and, where appropriate, in associated academic publications, unless they request otherwise.

---

*Last reviewed: 2026-05-05*
