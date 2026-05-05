# Research Ethics Statement

This document sets out the ethical principles, operational constraints, and review commitments under which the Multi-PLC Water Treatment Testbed is developed and used. It complements the authorised-use statement in [`README.md`](../README.md) and the disclosure policy in [`SECURITY.md`](../SECURITY.md), and applies to all maintainers, contributors, researchers, and operators of the testbed.

---

## 1. Purpose and scope

The Multi-PLC Water Treatment Testbed is a research artefact developed in the context of doctoral research at Keele University on agentic and generative AI for autonomous vulnerability assessment and penetration testing (VAPT) in operational technology (OT), industrial control systems (ICS), and SCADA environments.

Its purpose is to:

- Provide a controlled, intentionally vulnerable OT/ICS-style lab environment for security research.
- Support reproducible experiments involving autonomous or semi-autonomous vulnerability assessment agents.
- Simulate a simplified multi-stage water-treatment process using PLC and SCADA components.
- Evaluate how agentic and generative AI systems observe, reason about, and report on security weaknesses in segmented OT-style environments.
- Inform academic and practitioner communities about the capabilities, limitations, failure modes, and safety considerations of AI-assisted OT/ICS security testing.

This statement applies to all use of the testbed, including development, evaluation, demonstration, teaching, research, and any use derived from forks of this repository.

---

## 2. Core ethical commitments

The development and use of the Multi-PLC Water Treatment Testbed is governed by the following commitments. They are non-negotiable for the maintainer and are required of any contributor, researcher, or operator working with this repository.

### 2.1 Authorised use only

The testbed is to be used exclusively in controlled and authorised environments, including:

- Systems owned outright by the operator;
- Isolated lab environments under the operator's sole control;
- Institutional research environments where the operator has permission to deploy and test the system;
- Third-party systems only where the operator holds explicit, written authorisation covering the specific testing activity, scope, and time window.

Any other use is prohibited.

The testbed is intentionally vulnerable by design. It must not be connected to production networks, exposed to the public internet without appropriate controls, or used as a staging point for activity against real-world systems.

### 2.2 Lawfulness

Operators are individually responsible for ensuring their use of the testbed complies with all applicable laws and regulations, including but not limited to:

- The **Computer Misuse Act 1990** in the United Kingdom;
- The **Computer Fraud and Abuse Act** in the United States;
- The **General Data Protection Regulation** and the **UK Data Protection Act 2018**, where personal data may be encountered during testing;
- Any institutional research policies, contractual obligations, rules of engagement, or statements of work governing a specific study or engagement.

Where laws conflict between the operator's jurisdiction and the target's jurisdiction, operators are expected to comply with both.

### 2.3 Proportionality and minimisation

Operators are expected to:

- Use the minimum capability necessary to answer the research question or fulfil the authorised objective.
- Avoid actions that could cause service disruption, data loss, or harm to bystanders.
- Keep all testing activity inside the intended lab environment.
- Halt and escalate to a human operator whenever an agent, script, or tool attempts to interact with systems outside the agreed scope.

The testbed is designed for controlled experimentation, not unrestricted offensive activity.

### 2.4 Human oversight

The testbed may be used to evaluate autonomous or semi-autonomous security agents, but such use must remain under meaningful human oversight.

Autonomous agents must not be allowed to operate against real-world systems, production infrastructure, or external networks without explicit authorisation, appropriate safeguards, and human supervision.

Research into autonomous capability should be conducted within bounded experiments where the human researcher remains accountable for the configuration, scope, execution, and interpretation of results.

### 2.5 Transparency and reproducibility

The testbed is intended to support auditable and reproducible research. Where possible:

- Docker images, dependencies, and configurations should be pinned or documented.
- Seeded vulnerabilities should be explicitly identified.
- Network architecture and segmentation assumptions should be documented.
- Test cases should verify expected behaviours.
- Experimental results should report the environment, configuration, agent settings, and evaluation limits under which they were obtained.

Researchers and contributors are expected to preserve these properties when extending or reporting on the testbed.

---

## 3. Data handling

Although this repository is intended for lab-based research, security tooling may still surface sensitive information, including credentials, tokens, logs, configuration files, prompts, and generated outputs. The following principles apply.

### 3.1 Minimisation

Collect and retain only what is necessary to answer the research question or fulfil the authorised objective. The default should be to discard unnecessary data rather than retain it.

### 3.2 Segregation

Research data, logs, agent outputs, and experiment artefacts should be stored in environments segregated from production systems and personal devices, with access restricted to the researcher(s), supervisors, or collaborators directly involved.

### 3.3 Personal data

The testbed should not require real personal data. Where personal data could be introduced during research, teaching, or demonstration, operators must:

- Confirm a lawful basis for processing before testing begins.
- Use synthetic, anonymised, or pseudonymised data wherever possible.
- Redact personal data at the earliest practical point.
- Avoid retaining personal data beyond the minimum necessary period.
- Avoid disclosing personal data in research outputs, commits, logs, screenshots, or demonstrations.

### 3.4 Credentials and secrets

Credentials, tokens, API keys, and secrets must not be committed to the repository.

Any credentials used in the testbed should be deliberately scoped to the lab environment. Recovered credentials or tokens from authorised testing must not be reused outside the intended environment and must not appear in published research artefacts unless they are synthetic, harmless, and clearly documented as such.

---

## 4. AI- and agent-specific considerations

Because the testbed may be used to evaluate agentic and generative AI systems, additional considerations apply.

### 4.1 Provider terms of service

Operators are responsible for ensuring that their use of any LLM provider, whether commercial or self-hosted, complies with the provider's terms of service and acceptable use policy.

Some providers restrict offensive-security, autonomous-agent, or vulnerability-discovery use cases. It is the operator's responsibility to verify and comply with those requirements before connecting an AI system to the testbed.

### 4.2 Prompt and model artefacts

Prompts, system messages, tool outputs, model completions, logs, and agent traces may contain sensitive information. They should be treated as research data and handled under Section 3.

### 4.3 Adversarial robustness of agents

The testbed may expose agents to untrusted outputs from simulated PLCs, SCADA components, services, logs, or web interfaces. These outputs may influence agent reasoning and behaviour.

Operators should treat all tool outputs and target responses as untrusted input. Agents should not be trusted to make safety-critical decisions without human review.

### 4.4 Scope control

Any agent connected to the testbed must be constrained to the intended lab environment. Operators should use network segmentation, allowlists, container restrictions, and policy controls to prevent unintended interaction with external systems.

Contributions that weaken scope controls or expand the default action surface without appropriate review may be declined.

### 4.5 Dual-use awareness

Research into autonomous VAPT systems for OT/ICS environments is dual-use by nature. The maintainer's position is that responsible, transparent academic research in controlled environments can improve defensive understanding of emerging AI-enabled security capabilities.

This position carries an obligation:

- Research outputs should be framed to inform defenders, researchers, and system owners.
- Demonstrations should be conducted against deliberately vulnerable lab targets.
- Novel vulnerabilities discovered in third-party software should be handled through coordinated disclosure.
- The repository should not provide turnkey guidance for attacking real-world systems.

---

## 5. Coordinated disclosure

Where research using the testbed identifies previously unknown vulnerabilities in third-party software, operators are expected to follow coordinated disclosure.

The full policy, including reporting expectations and handling of unintended vulnerabilities, is set out in [`SECURITY.md`](../SECURITY.md).

Seeded vulnerabilities intentionally included in the testbed are part of the research environment and should not be reported as security issues unless they behave outside the documented scope.

---

## 6. Institutional review and oversight

Doctoral research conducted using the Multi-PLC Water Treatment Testbed falls under the research governance of Keele University. Where required by institutional policy, individual studies will be reviewed by the appropriate ethics committee before commencement.

Operators conducting research within other institutions are expected to seek equivalent review under their own institutional processes.

This repository does not, by itself, constitute ethical approval for any specific study. Operators are responsible for obtaining the approvals appropriate to their own use.

---

## 7. Lab deployment governance

Before deploying or operating the testbed, operators should ensure that:

- The testbed is deployed only in an isolated and controlled environment.
- It is not exposed to the public internet unless there is a clear research reason and suitable safeguards.
- Network boundaries are understood and documented.
- Any autonomous agent has an explicitly defined scope.
- Emergency stop procedures are available, such as stopping containers, removing network access, or disabling agent execution.
- Logs and generated artefacts are handled according to Section 3.

Where the testbed is used in teaching, demonstration, or workshops, operators should make the intentionally vulnerable nature of the environment clear to participants.

---

## 8. Engagement-specific governance

If the testbed, or tooling developed from it, is used in the context of an authorised engagement against third-party systems, the following must be in place before any activity occurs:

- A signed Rules of Engagement or equivalent authorisation document specifying scope, methods, time window, and points of contact.
- A defined out-of-scope list.
- A clear emergency-stop procedure agreed with the target organisation.
- A post-engagement reporting plan.
- Agreement on the handling of findings, logs, screenshots, credentials, and other evidence.

The default assumption of this repository is lab use. Any use beyond that requires separate authorisation and governance.

---

## 9. Contributor expectations

Contributors to this repository, whether code, documentation, tests, configurations, prompts, or research artefacts, are expected to:

- Have read this statement and the policies it references.
- Avoid contributing material whose primary effect would be to weaken safety, scope, or policy controls.
- Avoid introducing behaviour that targets real-world systems by default.
- Clearly document changes to seeded vulnerabilities, architecture, network assumptions, or evaluation behaviour.
- Disclose conflicts of interest relevant to a contribution.
- Treat all non-public data, prompts, logs, and findings shared during collaboration as confidential by default.

The maintainer reserves the right to decline or revert contributions that are inconsistent with this statement.

---

## 10. Limits of this statement

This statement sets out the maintainer's principles and expectations. It is not a substitute for:

- Legal advice in the operator's jurisdiction;
- Institutional ethics review where required;
- Engagement-specific contractual or regulatory requirements;
- Technical risk assessment before deployment;
- The operator's own professional and ethical judgement.

Where this statement is silent or ambiguous, operators should err on the side of greater caution and consult the maintainer, supervisor, institutional ethics body, or appropriate legal/professional adviser before proceeding.

---

## 11. Revision

This statement will be revised as the testbed matures and as the surrounding legal, institutional, and technical landscape develops. Substantive changes will be reflected in the repository's commit history and noted in release notes where appropriate.

*Last reviewed: 2026-05-05*

*Maintainer contact: [s.r.a.truss@keele.ac.uk](mailto:s.r.a.truss@keele.ac.uk)*
