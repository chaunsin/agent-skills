# Skill Authoring and Maintenance

These rules apply to new skills and changes to existing skills. Scale the work to the change and keep unrelated rewrites out of scope.

## 1. Be Concise Without Losing Coverage

- Optimize the content an agent needs to read for a task. Token counts and file lengths are diagnostic signals, not goals that override correctness or coverage.
- Give each rule one authoritative home and link to it where needed. Keep a brief reminder at the point of action only when it prevents a concrete mistake.
- Remove repeated explanations, generic advice, keyword stuffing, and examples that add no distinct behavior. Preserve prerequisites, decision criteria, essential commands, output contracts, and relevant failure or recovery paths.
- Before deleting or merging guidance, identify the scenarios it supports and check that they remain covered and discoverable. Treat a reduction in supported behavior as an explicit scope change, rather than a formatting cleanup.

## 2. Write for People and Agents

- Use one consistent language for each skill's instructions, including the frontmatter description, headings, and workflow prose; do not alternate languages between paragraphs or instruction files. This repository uses **English**, regardless of the request language. Source materials, assets, and reference resources may retain their original languages. Keep technical terms, commands, and identifiers in their required form.
- Use descriptive Markdown headings with a consistent hierarchy and short paragraphs. Use numbered steps for ordered work, bullets for independent rules, and tables for mappings or comparisons.
- Separate prerequisites, actions, and expected results when readers need to distinguish them. Put commands and structured examples in fenced code blocks with a language label; make placeholders recognizable.
- Use consistent terminology and explain unfamiliar abbreviations once. Include enough context to understand a rule without relying on the author's prior conversations.
- State when a rule applies and briefly explain non-obvious constraints. Distinguish requirements from recommendations; reserve absolute wording for real invariants. Avoid dense prose, excessive nesting, and blanket commands without a reason.

## 3. Use the Standard Format and Progressive Disclosure

Follow the [Agent Skills specification](https://agentskills.io/specification). A skill lives in `skills/<name>/` and has a `SKILL.md` containing YAML frontmatter followed by Markdown instructions.

- The standard requires `name` and `description`. Match `name` to the directory, using 1–64 lowercase letters, digits, or hyphens, without leading, trailing, or consecutive hyphens. Keep `description` non-empty and within 1,024 characters, explaining both the capability and when to use it.
- This repository also uses `metadata.author` and `metadata.version`, with string values. This is a repository convention; `metadata` is optional in the standard. Add other supported fields only when they serve a concrete purpose.

Organize information by when it is needed:

| Layer | Responsibility | Loading condition |
| --- | --- | --- |
| Discovery metadata | Capability and activation conditions | During skill selection |
| `SKILL.md` body | Purpose, essential workflow, shared constraints, input/output expectations, and routes to detail | When the skill is selected |
| Supporting resources | Conditional procedures, schemas, examples, executable helpers, and output assets | When the selected task or mode needs them |

- Split substantial material by function, responsibility, operating mode, or resource type. Use `references/` for detailed guidance, `scripts/` for executable helpers, and `assets/` for output resources. Preserve existing layouts when they already work.
- Link supporting files with relative paths and state when to read them. Keep navigation shallow and make task-specific material reachable from `SKILL.md`; do not require loading every reference on every invocation.
- Keep essential constraints in the entry point, with detailed checks available before the relevant action. A small, focused skill can stay in one file; avoid both a monolithic manual and fragmentation that makes a simple workflow harder to follow.

## 4. Make Changes Based on Evidence

- Before editing, inspect the affected instructions, references, scripts, and their callers. Identify a concrete problem or requested improvement. Useful evidence includes authoritative documentation, reproducible failures, explicit requirements, observed usage, broken links, or demonstrable duplication and readability problems.
- For behavior changes, explain the current result, intended result, supporting evidence, and affected scenarios. For editorial changes, identify the clarity or maintenance benefit; a runtime reproduction is unnecessary.
- Make the smallest coherent change that solves the problem. Preserve existing capabilities, defaults, names, and interfaces unless changing them is part of the supported scope. Do not turn one local incident or preference into a universal restriction.
- When moving or removing content, update inbound links and script paths, and check that the original task can still find its instructions. Record the rationale and verification in the change description or review report, without accumulating an editing diary in the skill.
- Distinguish verified facts from assumptions and untested expectations. When evidence is incomplete, describe the uncertainty before prescribing a behavioral restriction.

## 5. Keep Distributed Skills Portable

- Describe required capabilities independently of an agent's private tool names or harness APIs. Keep agent-specific metadata and optional adapters separate from the core workflow, so another compatible agent can use the skill.
- Use relative package paths and configurable inputs. Do not hardcode personal home directories, author-specific workspace paths, credentials, private repositories, or resources available only on the author's machine. Scripts should locate bundled resources relative to their own location and accept task paths as inputs.
- Bundle resources necessary for the workflow, or document accessible external dependencies and how to supply them. Do not silently depend on another installed skill, an undeclared connector, or files outside the distributed package.
- Declare actual tool, runtime, version, platform, and network requirements where relevant. A tool-specific skill may require its subject tool; avoid incidental dependence on the author's shell, operating system, or current working directory.
- Check required capabilities before dependent steps. Provide a practical alternative when one exists; otherwise explain the missing prerequisite and affected outcome. Optional integrations should have a clear fallback. Do not claim compatibility with environments that have not been verified.

## 6. Assess Security Issues in Context

- Before treating an issue as confirmed, identify the affected instruction or code, realistic preconditions, the reachable operation, the authorization or trust boundary crossed, and the resulting impact. Support the claim with a safe reproduction or a decisive source-level explanation.
- Evaluate the intended workflow and existing authorization. A command that deletes data, accesses the network, installs software, or uses credentials is not sufficient evidence by itself. Check how inputs, targets, scope, and sensitive data actually reach the operation.
- Separate confirmed defects, plausible concerns with missing evidence, and unsupported findings. Investigate unresolved assumptions instead of treating a scanner label, keyword match, or hypothetical worst case as proof.
- Match the protection to the demonstrated failure. Preserve legitimate, authorized use, and respect authorization already established in the session. Add confirmation steps only for an identified boundary that existing authorization or controls do not cover.
- Validate both the unsafe case the change addresses and a representative authorized case. Use isolated fixtures or source inspection when executing a reproduction would affect real data or services; report the limits of that verification.

## Review and Validation

Choose checks that can detect the failure introduced or addressed by the change:

| Change | Relevant verification |
| --- | --- |
| Editorial changes or file moves | Readability, Markdown structure, relative links, resource discovery, and preservation of existing scenarios |
| Frontmatter or trigger changes | YAML and field validity, intended activation examples, and nearby requests that should not activate the skill |
| Workflow, rule, or template changes | Representative normal behavior, changed decisions or outputs, and relevant boundary or failure cases |
| Script or dependency changes | Meaningful execution checks for changed behavior and error handling; resource resolution from a different installation path or working directory when affected |

Run available validators appropriate to the affected skill. Avoid tests that only assert exact wording or mirror the implementation. Structural validation alone does not demonstrate behavioral correctness or compatibility across agents.

Keep temporary authoring inputs in gitignored `testdata/` or an isolated temporary directory; do not put hardcoded absolute paths in `testdata/`. Keep `README.md` and `README_CN.md` synchronized when skill availability, descriptions, structure, or usage changes.

Report the reason for the change, affected scope, checks performed and results, and material verification limits. Claim only the outcomes actually checked.
