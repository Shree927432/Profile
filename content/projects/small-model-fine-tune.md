---
title: Fine-tuning a small language model, in public
year: 2026
summary: In progress. Thirty days to a LoRA fine-tune of a small Qwen model that beats the base model on a held-out test set.
tags: [machine learning, lora, in progress]
links:
  live: ""
  source: ""
cover: ""
featured: false
order: 3
---

Started 19 October 2026. The target, by 17 November: a small Qwen model, fine-tuned with LoRA on about a hundred examples I wrote and reviewed myself, that measurably beats the base model with a prompt on a test set it never saw. Done means a public repo with the dataset, the config, a scorecard for the base model, the fine-tuned model and one frontier model, and a loss curve I can explain.

The order matters, so the first two weeks are not fine-tuning. They are building the pieces by hand: a tiny autograd engine, a character-level model, a transformer from scratch, then LoRA on a single linear layer where I can check that step zero gives the same output as the frozen model. Only then the real tools. The rule is that I type every line and run after every change. AI explains errors after fifteen minutes stuck and reviews code I wrote. It does not write the training code.

This page will get the repo link, the scorecard and the failures as they happen. If the fine-tuned model does not beat the base model, that goes here too.
