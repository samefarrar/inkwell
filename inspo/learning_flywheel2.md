# I Taught Claude Every’s Standards. It Taught Me Mine.
_Was this newsletter forwarded to you? [Sign up](https://every.to/account) to get it in your inbox._

* * *

The first time I pasted a draft of an essay I’d written into the AI Every ﻿[editor](https://every.to/c/ai-guides)﻿ and it told me, “Spark is in the right place,” I practically whispered, _Thank God_.

After weeks of error messages and failed demos, that tiny seal of approval proved something I’d started to doubt: Maybe you really could teach a machine to spot what makes Every’s writing work.

The relief was technical—finally, a version that didn’t [collapse](https://every.to/working-overtime/how-i-successfully-failed-at-my-first-ai-operations-project) the moment I touched it—but it was also personal. It felt almost like a pat on the head from a real-life editor. I knew exactly how the feedback was generated, based on the examples I’d chosen, the values I’d spelled out, and the rules I’d written down. Still, when the system returned its blessing, I felt proud.

Previously, I described the [winding path](https://every.to/working-overtime/how-i-successfully-failed-at-my-first-ai-operations-project) to building Every’s AI editor from a technical perspective. This time, I want to talk about what it took to teach AI Every’s taste—collecting examples, writing down patterns, and translating our instincts into a playbook the system I set up as a [Claude project](https://www.anthropic.com/news/projects) could follow.

I was surprised by how clearly my own judgment came into focus once I tried to write it down for AI. When you can teach taste to a machine, you’re forced to make it legible for yourself. Some rules you already know; others only reveal themselves through explaining. The Claude project gave me the vessel, but I had to decide what belonged inside.

[![Uploaded image](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/advertisements/900/optimized_a547d4c0-1512-4201-afb6-1ba81b5d80e1.png)](https://framer.link/every)

#### **Vibe code your marketing page**

Your small team should focus fully on what matters—building the next big product. Let Framer take care of your marketing page. Use the tool to vibe code a website that feels authentic to your brand, with all the tools you need including SEO optimization, built-in analytics, and localization. Spend more time on the things that will actually make a difference to your customers.

Before you can teach taste, you have to define it
-------------------------------------------------

When I first [taught an AI editor](https://every.to/working-overtime/how-to-keep-your-writing-weird-in-the-age-of-ai), the only writer it had to worry about was me. The version I built for my column, [Working Overtime](https://every.to/working-overtime), was tuned to its quirks: Start with a problem I was having, use personal stakes to frame insight, surface a bigger cultural pattern, land on a sticky phrase. If my piece is missing one of these components, my editor will call it out. These rules made sense for me, but they didn’t belong in Every’s rulebook.

In order to adapt the editor so that it worked for the team, I had to change my relationship with my own opinions. It was no longer enough to encode what I personally liked or thought was good. I had to draw a line between my own preferences and Every’s values, deciding which instincts deserved to become rules that applied to everyone. I had to collect evidence beyond my own hunches: the essays CEO **Dan Shipper** had flagged as canonical, the ones the data told us our audience couldn’t stop reading, the pieces we all pointed to as “this is what Every sounds like.” Then I dropped those examples into ChatGPT (I migrated to Claude after the release of [Opus 4](https://every.to/vibe-check/vibe-check-claude-4-sonnet), but we’re reaching back in time) and asked the model to tell me what it saw.

The results read like an X-ray of Every’s signature moves. Strong introductions followed a rhythm: the spark of the idea on top, stakes established within 150 words, a quick zoom out, then a thesis pointing forward. Abstraction worked best when grounded in detail. Endings didn’t recap what had come before; they reframed.

Some of this we already knew. We’d been workshopping headline-subheading-introduction alignment in editorial meetings for months, reviewing each published piece and talking through how each component drew the reader into the piece (or didn’t). But seeing those judgments summarized in the chat window turned instinct into something visible, structured, and transferable.

Patterns alone don’t make a voice. To capture Every’s, I wrote in the three principles no model was going to surface on its own: optimistic realism, intellectual generosity, and conversational authority. Here, I let my own judgment creep back in. I had certain opinions about what makes Every _Every,_ and I wanted those values to be baked into the editor’s DNA. Optimistic realism keeps us from lapsing into cynicism. Intellectual generosity makes sure we argue in a way that invites people in, not pushes them out. Conversational authority reminds us that confidence can coexist with humility. Without those anchors, the rules risked describing a style, not a voice. Style is the “how”: the choices of syntax, rhythm, and imagery that shape the prose. Voice is the “why”: the convictions that give those stylistic choices meaning.

How to boss a robot around
--------------------------

Patterns and values on paper were a start, but they didn’t mean much until I could teach the system how to use them. Models don’t understand a rule like “spark should be on top” unless you spell out what “spark” means, how to find it, and what to do when it’s buried. The next step was translating taste into instructions precise enough that an AI could enforce them.

To help, I leaned on Anthropic’s [prompt builder](https://console.anthropic.com/dashboard), a feature in the Anthropic Console that generates optimized prompt instructions for you based on information you give it about your goals. I pasted the list of principles and rules I’d developed with ChatGPT into the prompt builder, and it translated that content into a set of custom instructions that, when hooked up to the Claude project via project files, would act as the editor’s brain**.**

[![I dropped the principles I’d developed with ChatGPT into the Anthropic prompt generator, added a line at the beginning about what output I wanted, and got a set of custom instructions that I could input to the Claude project to tell it how to behave. (All screenshots courtesy of the author.)](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_1acdc8d9-78eb-412a-8c2e-5b49f1ce7cd1.png)](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_1acdc8d9-78eb-412a-8c2e-5b49f1ce7cd1.png)

I dropped the principles I’d developed with ChatGPT into the Anthropic prompt generator, added a line at the beginning about what output I wanted, and got a set of custom instructions that I could input to the Claude project to tell it how to behave. (All screenshots courtesy of the author.)

The prompt builder helped me turn Every’s DNA from principles into checklists the editor could run through systematically. The vague directive to “put the spark up top” became a set of three scenarios for the editor to pick from: Spark is in the right place, buried spark is found, and spark needs sharpening. "Use active voice" transformed from a general reminder into a systematic audit—count every instance, flag its location, and provide the exact rewrite.

At first, the prompt builder seemed to have nailed it—comprehensive instructions, all generated automatically. But when I set up the project and started testing it with real drafts, I kept noticing aspects that didn’t feel quite right. It would flag an issue, but not explain why it mattered. It would recommend a fix, but not articulate why it was better. I went through dozens of rounds of trial and error—inputting drafts, evaluating outputs, spotting gaps, then updating the instructions to fill them. A few of the key rules I added:

1.  **Check everything.** _“You must evaluate the draft against all guidelines. Missing issues is unacceptable.”_ No skipping, no “close enough.”
2.  **Work systematically through phases.** The editor can’t jump around based on what catches its attention—it has to move through drafts in a prescribed order.
3.  **Provide specific fixes.** _“For every issue identified, provide an exact rewritten line in Every’s voice.”_ Vague notes aren’t helpful—every flag needs a concrete rewrite.

Each instruction tightened the system and made it more predictable. Early in my experimentation, before I added the custom instructions, I found that the editor veered from nitpicky to vague. An Every-wide system meant to enforce standards across multiple writers, columns, and content types needed to be consistent. Consistency made the feedback reliable, even when I didn’t agree with it. It gave writers a stable first reader—one that might be blunt, but never arbitrary.

What happens when you hit ‘Enter’
---------------------------------

The Every AI editor that finally worked didn’t look like the [sleek, vibe-coded solution](https://every.to/working-overtime/how-i-successfully-failed-at-my-first-ai-operations-project) I’d imagined. The workflow was simple: Open the shared Claude project, paste your draft with headline and subheading options, and hit “Enter.”

The output is a report—a map of the decisions ahead. It highlights the editorial patterns we wrestle with most often at Every and arranges them into a sequence writers can act on.

**Spark assessment.** The editor hunts for the line that makes the piece come alive. Sometimes it’s already on top. Sometimes it’s hiding deep in the draft. Sometimes it’s there but needs sharpening. The editor “knows” that all three of these are possibilities. It’s set up to determine which situation applies and then propose a fix based on that assessment.

[![The AI editor spots an interesting “spark” buried in paragraph 10 that it thinks I should move to paragraph three.](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_3ebeb0bb-cb83-4eab-b5ab-cb1002e8daf9.png)](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_3ebeb0bb-cb83-4eab-b5ab-cb1002e8daf9.png)

The AI editor spots an interesting “spark” buried in paragraph 10 that it thinks I should move to paragraph three.

**Critical fixes.** These are the structural moves. A weak headline gets a stronger option. A repeated explanation is quoted in each place it appears, with guidance on which to cut. A claim without evidence is flagged with an example of what kind of support to add. Every fix comes paired with a suggested rewrite in Every’s voice.

**Line-level refinement map.** A guided walk through the draft, line by line. Passive voice, undefined jargon, and floating abstractions are quoted directly, each followed by a sharper alternative.

[![The editor gives me a list of line-level refinements I should make before submitting.](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_f5d9ac8e-58aa-4997-b9c4-4545772b1e96.png)](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_f5d9ac8e-58aa-4997-b9c4-4545772b1e96.png)

The editor gives me a list of line-level refinements I should make before submitting.

**Implementation roadmap.** A proposed order of operations. Step one: Fix the opening. Step two: Add evidence. The editor distilled the 19 issues it had flagged into a sequence of five manageable steps.

**Final gut check.** A reflection on what the piece will achieve once the changes are made: why the fixes matter, and what kind of effect they are likely to have on Every’s readers.

[![The editor ends its feedback on a positive note with what the fixes will do for the piece and why it will resonate with Every readers once it’s ready.](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_6275596a-b4e7-4ea4-a865-ea9b27fc458b.png)](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_6275596a-b4e7-4ea4-a865-ea9b27fc458b.png)

The editor ends its feedback on a positive note with what the fixes will do for the piece and why it will resonate with Every readers once it’s ready.

Editing as a choice, not a shortcut
-----------------------------------

On paper this might sound like workflow software. In practice, it creates a consistent structure for editorial judgment. Each report surfaces choices that usually live in the background, makes them explicit, and returns them to the writer.

That handoff is key. You could take the feedback and direct the AI to generate a clean draft instantly, but that isn’t how we use it. At Every, writers are expected to move through the report themselves. The friction is deliberate. It forces ownership of the work.

With each edit, writers have to make a decision: Accept, reject, or revise. That pause is part of the editing. It sharpens your sense of which changes strengthen the piece and which push it off course. The AI editor provides structure. The writer provides intent. Together, those two forces produce work that feels rigorous without [losing its edge](https://every.to/working-overtime/how-to-keep-your-writing-weird-in-the-age-of-ai).

[![Source: Every illustration.](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_f30ea94e-ef1a-4933-9197-d9d44478017d.png)](https://d24ovhgu8s7341.cloudfront.net/uploads/editor/posts/3738/optimized_f30ea94e-ef1a-4933-9197-d9d44478017d.png)

Source: Every illustration.

The taste in the machine
------------------------

I’ll tell you this much: Now that I have it, you’ll tear Claude—and the Every AI editor that lives inside of it—out of my cold, dead hands. Same for my Working Overtime project. They’ve changed how I write by reminding me of what I value on the page and then holding me accountable to live up to it. I think more carefully about what I put down in writing because I know the editor will interrogate it. I send drafts to my editors with more confidence because I’ve already pressure-tested them against a consistent set of standards. My editors can review my drafts knowing that the basics have been covered, and they’re free to focus on higher-level questions about angle, audience, and intent.

That’s why I resist the storyline of AI as a replacement for human labor. What I’ve built demands _more_ judgment from me, not less. These systems create pressure to articulate the reasoning behind the work—the gut calls, the unwritten norms, the instincts that usually stay hidden. It’s tempting to treat AI like a vending machine: Type a clever prompt, collect a finished product, move on. My experience has been slower and more demanding. To build the editor, I kept circling the same hard questions, like what actually makes a spark feel alive, or how much scaffolding an anecdote needs before it earns its keep. Each test and iteration forced me to drag instincts I usually leave unspoken into the open.. The time commitment was significant, and the time made me better.

So much of what we do at work, editing or otherwise, runs on tacit judgment. Working with AI turns [the invisible into the explicit](https://every.to/chain-of-thought/what-i-do-when-i-can-t-sleep). If you want to see your own instincts in sharper focus, try teaching an AI what “good” looks like in your work. The exercise will surface rules you didn’t know you were following—and challenge you to decide which ones you believe.

* * *

**_Katie Parrott_** _is a staff writer and AI editorial lead at Every. You can read more of her work in [her newsletter](https://katieparrott.substack.com/)._

_To read more essays like this, subscribe to [Every](https://every.to/subscribe), and follow us on X at [@every](https://twitter.com/every) and on [LinkedIn](https://www.linkedin.com/company/everyinc/)._

_We [build AI tools](https://every.to/studio) for readers like you. Write brilliantly with_ **_[Spiral](https://spiral.computer/?utm_source=everyfooter)_**_. Organize files automatically with_ **_[Sparkle](https://makeitsparkle.co/?utm_source=everyfooter)_**_. Deliver yourself from email with_ **_[Cora](https://cora.computer/)_**_._

_We also do AI training, adoption, and innovation for companies. [Work with us](https://every.to/consulting?utm_source=emailfooter) to bring AI into your organization._

_Get paid for sharing Every with your friends. Join our [referral program](https://every.getrewardful.com/signup)._
