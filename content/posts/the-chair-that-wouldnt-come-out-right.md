---
title: The Chair That Wouldn't Come Out Right
date: 2026-10-29
summary: What a week of making a language model build 3D furniture taught me about the gap between language models and world models, and where that argument stands.
tags: [essay, ai]
---

I spent a week watching one of the best language models available fail to build a chair.

Not a chair in general. A specific one: the Herman Miller Aeron, in the pale grey called Mineral, for the 3D room that is slowly becoming this website. The model had the official dimensions. It had Herman Miller's product photos from five angles. It had a brief listing every feature that makes an Aeron an Aeron: the wedge-shaped back that is wider at the top, the Y-shaped support behind the lumbar, the seat frame with the rolled front edge, the polished five-star base. It had ninety minutes, then two more rounds of fixes.

![Our Aeron after three rounds, rendered on its own](/images/posts/the-chair/chair-final.jpg)

*The chair after three rounds. From here it is an Aeron.*

It produced something that, from across the room, is an Aeron. From up close it is a chair-shaped argument about what language models are and are not. The seat is a tray with a rim. The arms are the right idea in the wrong thickness. The mesh is a grid. Every one of those misses has a cause I can name, and the causes are the subject of this essay, because they turn out to be the same ones that a few thousand researchers and a few billion dollars are currently arguing about under the heading *world models*.

## Two kinds of model

A language model is trained to predict the next piece of a sequence. Feed it everything written, and it learns the statistics of what follows what, at a depth that turns out to include an enormous amount of knowledge about the world, because the world is what the writing is about. Ask it what an Aeron is and it tells you. Ask it for the Blender code that makes a five-legged base and it writes it, correctly, first time.

A world model is trained to predict what the world will look like next, given its current state and an action. The idea is older than the current wave. Kenneth Craik proposed in 1943 that the brain carries a "small-scale model" of reality it uses to try out actions before committing to them. In reinforcement learning the term has meant a learned simulator for decades. The modern form arrived in 2018, when David Ha and Jürgen Schmidhuber published a paper called, simply, *World Models*: a small network learned a compressed representation of a video game, another learned to predict the next frame, and an agent trained entirely inside the resulting dream could then drive the real game. Danijar Hafner's Dreamer models extended the idea until a single agent could learn dozens of tasks, including collecting diamonds in Minecraft, by imagining the consequences of actions rather than trying them all.

The difference, then, is what the model holds. A language model holds a distribution over sequences of symbols. A world model holds a state, and a rule for how states change. Both are trained by prediction. They predict different things.

## The case that language models already have one

The obvious reply is that a model that can describe a chair, explain how its tilt mechanism works and write code to build its base must have some model of the world inside it. Where else would the right answers come from?

There is real evidence for this. In 2023, researchers trained a small GPT on nothing but transcripts of Othello games, sequences of moves with no board, no rules, no pictures, and then showed with probes that the network had built an internal representation of the board: which squares were occupied, and by whom. It had never been told there was a board. It inferred one, because a board was the simplest explanation for the sequences. A 2025 follow-up from the University of Copenhagen repeated this across seven model families up to Qwen2.5 and found the induced board layouts aligned with the real one at up to 99 percent accuracy. The *Othello world model hypothesis* has held up.

The same intuition drove OpenAI's framing of Sora in early 2024 as a step toward "world simulators": a video model that keeps objects consistent across frames must be modelling the space they move in. Google DeepMind's Genie 3, released in August 2025, pushed that further. Give it a text prompt and it generates a world you can walk through, at 720p and 24 frames a second, that stays consistent for several minutes, with memory reaching back about a minute. It is autoregressive, like a language model: each frame is predicted from the frames before it and the user's latest action. If that is not a world model, the words have no meaning.

## The case that they don't

The counter-evidence is just as concrete.

In 2024, a group at MIT and Harvard asked a different question: not *can the model answer*, but *is the model it uses coherent*? They trained transformers on turn-by-turn taxi directions through New York and found they gave near-perfect directions. Then they reconstructed the map implied by the model's behaviour. It was not Manhattan. It was a tangle of streets that do not exist and impossible flyovers, a structure that happened to produce correct outputs on the training distribution and fell apart as soon as streets were closed. Right answers, wrong world. They proposed the uncomfortable rule that follows: you cannot infer a coherent world model from good predictions alone.

Video models fail in the same way, just more photogenically. DeepMind's own Physics-IQ benchmark, released in early 2025, showed that models which produce visually convincing video score far below human judgement on whether the physics was right. They have learned what motion *looks like*, not what causes it. Genie 3's own limitations list is telling: a few minutes of coherence, a restricted set of actions, trouble with more than one agent. Impressive and brittle at once.

Yann LeCun has made the strongest version of the argument against for years, and in 2025 he bet his career on it. His case has two parts. The first is data efficiency: a language model reads the equivalent of hundreds of thousands of years of text to reach its level, while a child learns more about the physical world from a few years of looking. The second is that predicting pixels, or tokens, forces a model to spend its capacity on details that do not matter, the exact pattern of leaves in the wind, instead of the abstract state that does. His alternative, JEPA, predicts in a learned representation space instead: not *what will the next frame be*, but *what will the world's state be*. Meta's V-JEPA 2, released in June 2025, trained on a million hours of video and only 62 hours of robot data, and could then plan pick-and-place tasks on a real arm in environments it had never seen, at roughly 65 to 80 percent success, with no task-specific training. Meta's own benchmarks also showed it still well behind humans on basic physical understanding and on anything that takes long-term planning.

LeCun left Meta in late 2025 to found AMI Labs around this idea. In March 2026 it closed a seed round of $1.03 billion at a $3.5 billion valuation, reportedly the largest seed round in European history, with twelve employees. That is how seriously the money takes the argument.

## What exists right now

It helps to separate the demonstrations from the products, and both from the claims.

*Generating worlds.* Genie 3 (DeepMind) and Marble (World Labs, Fei-Fei Li's company, which raised $1 billion in February 2026) are the two visible flagships. Genie generates interactive video; Marble generates persistent 3D scenes as Gaussian splats you can export and walk around. Nvidia's Cosmos line is aimed at the same place from the robotics side: synthetic worlds to train machines in. All of them are good at *looking* like a place and weak at being a precise one.

*Image to 3D.* This is the corner I actually needed. Tencent's Hunyuan3D 2.5 and Microsoft's TRELLIS 2 will turn a few photos into a mesh in under a minute, and in 2026 the open models are competitive with the commercial ones. What they produce is a soft, approximately right object: melted edges, one fused lump instead of parts, textures baked onto the surface, and real trouble with thin and concave features, exactly the things an Aeron is made of. Usable as a background prop. Not usable as the chair.

*Robots.* This is where world models stop being a philosophical position and start being a product category. DeepMind's Gemini Robotics line went from a first release in March 2025 to version 1.5 in September and an ER 1.6 in April 2026, with spatial reasoning good enough to read instruments on a Boston Dynamics robot. Physical Intelligence's π series reached π0.7 in April 2026. Nvidia's GR00T N1.7 was pretrained on 20,854 hours of human first-person video. The pattern in all three: a vision-language model supplies the understanding of *what* and *why*; something learned from video and interaction supplies the *how*. None of them is a pure language model, and none of them is a pure world model.

## What is not possible yet

Four things, and they are the same four that bit me in Blender.

**Long horizons.** A minute of memory is the state of the art for generated worlds. Robot planners work over seconds. Nobody has a learned model that stays coherent over the hour it takes to build something.

**Precision and structure.** Generated geometry is a blob. Real objects are assemblies: fourteen named parts, a pivot the chair turns on, casters that roll. Turning a blob into that is still human work, or script work. The language model, for all its blindness, produces structure for free, because it writes code and code is structure.

**Evaluation.** How do you score a world model? Prediction error on pixels rewards the wrong things. Downstream task success is slow and expensive. I hit a tiny version of this problem: my test for whether the chair matched the photos compared silhouettes, and a chair that is mostly see-through mesh scores terribly even when it is right, because the camera saw through ours and not through theirs. If you cannot measure it, you cannot improve it on purpose. This is, I think, the quietest and most important bottleneck in the whole field.

**Data.** Video is plentiful; video *with actions and outcomes* is scarce. V-JEPA 2's 62 hours of robot data is a rounding error next to the trillions of tokens a language model reads, and that gap is the whole reason the robotics labs are collecting human first-person video by the tens of thousands of hours.

## The binary is a bad frame

The public debate is staged as LLMs versus world models, Hinton and Bengio versus LeCun, scale versus architecture. The models themselves are not following the script. Every frontier model is now trained on images and video as well as text; the word *language* in LLM is already a historical label. Genie 3 is a world model with a language model's architecture. Gemini Robotics is a language model with a body. Richard Sutton and David Silver's 2025 essay *The Era of Experience* argues that the next gains come from models learning from their own actions and consequences rather than from human text, which is a world-model thesis delivered by two of the people most associated with scaling.

My bet, held loosely: for the next few years, language models stay dominant in what people use, because most valuable work runs through text and code, the data is there, and the tooling compounds. World models become the next frontier through robotics, simulation and 3D, where the gap in spatial understanding is the whole problem and the prize is larger than chat ever was. And the thing that wins is a merger: one system that reasons in language and holds a predictive model of the world, with the labels fading. The pure text model is what gets replaced. The language ability does not.

## What the chair taught me

I did not expect a furniture project to be an experiment in this question, but it was, and the result is clean enough to write down.

Everything in my room that is made of boxes, cylinders and extrusions came out close to the real thing: a PC case, an audio interface, a keyboard with 81 separate keys, a Stream Deck. The model knows what those objects are, and it can describe them in code, and code is enough for shapes like that. Everything free-form failed on the first try: a mouse, then the chair. The model knows what a mouse is just as well. The knowledge was never the problem.

![The chair after the first ninety minutes, left, and after two fix rounds, right](/images/posts/the-chair/chair-first-vs-final.jpg)

*Left: the first ninety minutes. Right: after two rounds of fixes. The base, the back and the Y came right; the seat and the arms are still the model guessing at surfaces it cannot see.*

What fixed the mouse was not more intelligence. It was a 3D scan of the real mouse, free under a Creative Commons licence, three million triangles of actual surface. The model wrapped its own light shell onto it, built the wheels and buttons by code on top, and the result matched the real thing from every angle in one pass. It borrowed a piece of the world because it could not imagine one. That is the whole argument in one object.

![The 3D scan of the real mouse, left, and our model built on it, right](/images/posts/the-chair/mouse-scan-vs-ours.jpg)

*Left: the scan of a real MX Master 3S (by Sircher on Sketchfab, CC BY). Right: our mouse, a light shell fitted to that scan with the wheels, buttons and port built on top. The scan never ships; only the shell does.*

So here is what I think the bottleneck is, stated plainly. A language model building in 3D is working blind, by numbers, from photographs taken by a camera it cannot see, with a handful of low-resolution looks at its own output, in a time box a professional would laugh at. It fails on exactly the things that need a model of space: a surface that curves in two directions, a part that has to sit *inside* another, a thickness that has to feel right. It succeeds on exactly the things that can be written down. Give it a surface to fit, more and faster looks at what it made, and a measurement that rewards the right things, and it gets to the level of the mouse. Give it a human for the two sculpted pieces and it gets to the level of the chair I wanted.

That is not a story about a tool falling short. It is the precise shape of the hole that world models are supposed to fill, drawn in pale grey plastic, sitting in front of my desk.

![The room as it stands, with the chair in front of the desk](/images/posts/the-chair/room-with-chair.jpg)

*The room as it stands tonight. Everything on the desk was built by a language model writing Blender code; the grey boxes are the parts still to come.*

---

### Sources

Primary and first-hand:
- The build journal of this site's 3D room, October 2026 (the mouse, the chair, the compare scores).
- Craik, K. *The Nature of Explanation*, 1943.
- Ha, D. and Schmidhuber, J. *World Models*, 2018.
- Hafner, D. et al. *Dream to Control* (2019) and *Mastering Diverse Domains through World Models* (DreamerV3, 2023).
- Li, K. et al. *Emergent World Representations: Exploring a Sequence Model Trained on a Synthetic Task* (Othello-GPT), 2023; summary at [The Gradient](https://thegradient.pub/othello/).
- Yuan, Y. and Søgaard, A. *Revisiting the Othello World Model Hypothesis*, ICLR 2025 World Models Workshop, [arXiv 2503.04421](https://arxiv.org/abs/2503.04421v1); coverage at [The Decoder](https://the-decoder.com/new-othello-experiment-supports-the-world-model-hypothesis-for-large-language-models/).
- Vafa, K., Chen, J., Kleinberg, J., Mullainathan, S. and Rambachan, A. *Evaluating the World Model Implicit in a Generative Model*, 2024 (the New York taxi directions study).
- Motamed, S. et al. *Do generative video models understand physical principles?* (Physics-IQ), 2025.
- Silver, D. and Sutton, R. *Welcome to the Era of Experience*, 2025.
- Bender, E. and Koller, A. *Climbing towards NLU*, 2020 (the octopus argument).

Reporting checked on 2026-10-29:
- Genie 3: [The Decoder](https://the-decoder.com/google-deepminds-genie-3-generates-interactive-3d-worlds-that-stay-consistent-for-multiple-minutes/), [BDTechTalks on its limits](https://bdtechtalks.com/2025/08/07/deepmind-genie-3/), [Maginative](https://www.maginative.com/article/google-deepminds-genie-3-builds-interactive-worlds-from-a-text-prompt/).
- V-JEPA 2: [The Decoder](https://the-decoder.com/metas-latest-model-highlights-the-challenge-ai-faces-in-long-term-planning-and-causal-reasoning/), [Pure AI](https://pureai.com/Articles/2025/06/18/Meta-VJEP-2.aspx).
- AMI Labs' $1.03B seed: [TechCrunch](https://techcrunch.com/2026/03/09/yann-lecuns-ami-labs-raises-1-03-billion-to-build-world-models/), [SiliconANGLE](https://siliconangle.com/2026/03/10/yann-lecuns-new-startup-ami-labs-raises-1-03b-train-world-models/), [heise](https://heise.de/-11206350).
- The LLM-versus-world-model framing and LeCun's position: [aivancity](https://aivancity.ai/en/blog/?p=648293), [Apolo on JEPA's history](https://www.apolo.us/blog-posts/yann-lecuns-jepa-and-world-models-a-thirty-years-history), [StartupHub](https://www.startuphub.ai/news/figure-yann-lecun-strategic-position-vs-peer-2026-07-15).
- World Labs and Marble: [Radiance Fields on Marble 1.1](https://radiancefields.com/world-labs-releases-marble-1.1-and-marble-1.1-plus), [VKTR on the $1B round](https://www.vktr.com/ai-news/world-labs-raises-1b-to-advance-spatial-intelligence-and-3d-world-modeling/), [worldlabs.ai](https://worldlabs.ai/).
- Image-to-3D in 2026: [Pixazo leaderboard](https://www.pixazo.ai/leaderboard/ai-3d-model-generation), [RunDiffusion comparison](https://www.rundiffusion.com/ai-3d-model-generators), [Sorceress six-model test](https://sorceress.games/blog/rank-the-best-image-to-3d-model-ai-six-model-test).
- Robotics: [MarkTechPost on 2026 physical AI models](https://www.marktechpost.com/2026/04/28/top-10-physical-ai-models-powering-real-world-robots-in-2026/), [π0.7 on arXiv](https://arxiv.org/html/2604.15483v1), [a Gemini Robotics write-up](https://my-personal-site-bxp.pages.dev/blog/papers-2026-03-12-gemini-robotics-foundation-model/), [TWIML](https://twimlai.com/articles/the-robots-are-coming).
