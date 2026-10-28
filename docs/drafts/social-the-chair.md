# Social posts for "The Chair That Wouldn't Come Out Right" (2026-10-29)

Link: https://shrikantpawade.pages.dev/posts/the-chair-that-wouldnt-come-out-right
Image to attach: public/images/posts/the-chair/chair-first-vs-final.jpg (LinkedIn) and mouse-scan-vs-ours.jpg (X).

## LinkedIn

I spent a week making a frontier language model build a Herman Miller Aeron in Blender. It failed in a very specific way, and the way it failed is the clearest explanation I've found of the gap between language models and world models.

The setup: official dimensions, product photos from five angles, a brief listing every feature, ninety minutes, two rounds of fixes.

The result: from across the room, an Aeron. Up close, a seat that is a tray with a rim, arms the right idea in the wrong thickness, a mesh that is a grid.

What struck me is what did NOT fail. A PC case, an audio interface, a keyboard with 81 separate keys, a Stream Deck: all came out close to the real thing. They are boxes, cylinders and extrusions, and the model can describe those in code. The chair and a mouse are free-form surfaces, and the model cannot see them. It knows exactly what a mouse is. Knowledge was never the problem.

What fixed the mouse was not more intelligence. It was a 3D scan of the real mouse, free under Creative Commons. The model wrapped its own light shell onto it and the result matched from every angle in one pass. It borrowed a piece of the world because it couldn't imagine one.

That is the whole world-model debate in one object: LeCun's data-efficiency argument, the Othello and taxi-map studies, Genie 3, V-JEPA 2, the $1B seed rounds. I wrote it up, with what is possible today, what is not, and where I think it lands.

Essay: https://shrikantpawade.pages.dev/posts/the-chair-that-wouldnt-come-out-right

#AI #WorldModels #Blender #3D

## X (thread, 4 posts)

1/ I spent a week making a frontier LLM build a Herman Miller Aeron in Blender. It failed in a precise way, and the failure is the best explanation I have of the gap between language models and world models.

Essay, with pictures: https://shrikantpawade.pages.dev/posts/the-chair-that-wouldnt-come-out-right

2/ What came out right: a PC case, an audio interface, a keyboard with 81 separate keys. Boxes, cylinders, extrusions. Things you can write down in code.

What came out wrong: a mouse, then the chair. Free-form surfaces. The model knows exactly what they are. Knowledge was never the problem.

3/ What fixed the mouse wasn't more intelligence. A free CC-BY 3D scan of the real mouse. The model wrapped its own light shell onto it and matched the real thing from every angle in one pass.

It borrowed a piece of the world because it couldn't imagine one.

4/ A language model building in 3D works blind: by numbers, from photos taken by a camera it can't see, with a handful of low-res looks at its own output. It fails exactly where a model of space is needed.

That hole is what world models are meant to fill. The essay is the long version.

## X (single post, under 280 characters)

I made a frontier LLM build a Herman Miller Aeron in Blender for a week. Boxes and cylinders came out right; the chair didn't. A free 3D scan fixed the mouse in one pass. That gap is the whole LLM vs world model debate, in one object. Essay: https://shrikantpawade.pages.dev/posts/the-chair-that-wouldnt-come-out-right
