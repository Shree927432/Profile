---
title: CI diagnosis MCP server
year: 2026
summary: An MCP server that reads a failed GitHub Actions run and hands a coding agent the evidence, not a guess.
tags: [python, mcp, agents]
links:
  live: ""
  source: https://github.com/Shree927432/ci-diagnosis-mcp
cover: ""
featured: true
order: 1
---

When a CI run fails, a coding agent usually gets a wall of log and a hunch. This server does the reading first. It pulls the failed jobs' logs, finds the failing step, works out what failed (a test assertion, a compile error, a lint rule, a dependency, a timeout) and why it probably failed (this change, something pre-existing, a flaky test, the environment, an outside service), with a probability for each and the evidence behind it. It never calls a model. The agent reasons; the server supplies evidence and belief.

It started as a research prototype: a Bayesian agent that treats the cause of a failure as a hidden state and picks the next diagnostic action by expected information gain per unit cost. The MCP server is that idea made usable. Parsers cover the common test runners, compilers and linters across JavaScript, Python, Go and Rust. The accuracy corpus is 33 real failed jobs from public repositories, plus synthetic cases for the failures no public log happened to show.

What I learned: commit the fixture before the parser, so the test exists before the code that passes it. And a structured "not sure yet, fetch this next" is worth more to an agent than a confident wrong answer.
