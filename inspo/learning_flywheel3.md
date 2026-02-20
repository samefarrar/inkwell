# What Board Games Taught Me About Working with AI 
_TL;DR: In case you missed it, you can now see all of Every’s upcoming camps and workshops [in one place](https://every.to/events). Coming up this Friday: our [Compound Engineering Camp](https://every.to/events/compound-engineering-camp), where_ **_[Kieran Klaassen](https://every.to/@kieran_1355)_** _introduces the AI-native philosophy that helps Every ship products with single-person teams, and on February 24, learn Claude Code in one day in our [live, beginner-friendly workshop](https://claude101.every.to/) taught by_ **_[Mike Taylor](https://every.to/@mike_2114)_**_.—[Kate Lee](https://every.to/on-every/kate-lee-joins-every-as-editor-in-chief)_

* * *

I’d been stuck on trying to build my own writing agent for months when I found myself scanning my board game shelf. Suddenly, the problem wasn’t about AI anymore.

It was the end of [Think Week](https://every.to/context-window/give-yourself-a-promotion), Every’s twice-yearly retreat where we break to explore possibilities outside the flow of our regular work. The team was in a beach house in Panama, decked out in shorts and sunglasses with palm trees swaying in the background. I was under 10 inches of snow in Ohio, locked in a battle of wills with my dog about going outside.

From my laptop, I watched **[Austin Tedesco](https://every.to/@tedescau)**, Every’s head of growth, demo a dashboard he built in one day that pulls data from PostHog and Stripe and gives him a complete view of signups and subscription revenue. COO **[Brandon Gell](https://every.to/@brandon_5263)** showed off an AI CFO that helps him steer the company. Head of consulting **[Natalia Quintero](https://every.to/@natalia_2944)** shared Claudie, an AI agent that she and applied AI engineer **[Nityesh Agarwal](https://every.to/@nityesh)** had built in two weeks with nothing but Claude Code and a dream.

Meanwhile, my momentum had stalled out as badly as my attempt to get my passport renewed in time for the trip. It was a stark contrast to how I’d felt six months earlier. In July, I was on a roll: I’d built a [custom ChatGPT project](https://every.to/working-overtime/i-fed-my-essays-to-chatgpt-until-it-learned-my-voice) that ran my entire drafting process. I’d developed an AI editor that could [enforce Every’s editorial sensibilities](https://every.to/working-overtime/i-taught-claude-every-s-standards-it-taught-me-mine) and written specialized Claude prompts called [Skills](https://every.to/vibe-check/vibe-check-claude-skills-need-a-share-button) that the whole editorial team used. But around September the wind fell out of my sails, and it hadn’t quite been back since.

Watching my coworkers demo these systems made me want to take advantage of all [the new capabilities of Opus and Codex](https://every.to/vibe-check/codex-vs-opus), of [agent-native architectures](https://every.to/source-code/how-to-build-agent-native-lessons-from-four-apps) and the seemingly infinite possibilities popping up on all sides like Whac-A-Mole moles. I just had no clue where to start.

At the same time, my best friend and I were playing chicken about whether we’d brave the snow to get together. I scanned my board game shelf, stocked with everything from crowd pleasers like Wingspan and Codenames to five-hour behemoths that no one wants to play with me, ever. I was trying to decide what we’d play if she did come over… and then I was thinking about worker placement and area control and victory conditions.

What ensued was that strange, slightly vertigo-inducing feeling when two unrelated ideas fuse together in your head: What if I thought about my AI project as a board game?

The art and science of ‘the teach’
----------------------------------

I spent the holidays teaching my nephews board games. Over four days, the four of us—a nine-year-old, a seven-year-old, my mom, and me—played five different games. It’s not everyone’s idea of a good time, but it is mine.

I like to think I have what’s called “the teach” in board game lingo down to a science. Before you go into strategy, before “here’s how you beat your brother,” there’s a more basic question: What are the pieces, and what do they do? This little wooden person is called a meeple. When you place it, you’re claiming that road. This gem chip means you can afford more expensive cards. This sushi card is worth points if you collect three of them.

I knew I wanted to build a writing system that could take advantage of all these new capabilities and tools, but I wasn’t even clear on the parts I was working with. I had a Claude project with some custom instructions and a few Google Docs that I’d manually edit whenever I wanted to change something. It worked well enough. But it didn’t feel magical like those Think Week projects did.

I needed an example, a game I could study to help me understand the parts and what they might do. Fortunately, I already had one in mind.

The game on the shelf
---------------------

**[Cora](https://cora.computer/)** general manager **[Kieran Klaassen](https://every.to/@kieran_1355)** built a [compound engineering plugin](https://github.com/EveryInc/compound-engineering-plugin)—a software development system for Claude Code that gets smarter the more you use it. Every time you fix a bug or have a new insight, you write it down and feed it back to the AI. Over time, the system learns your preferences and grows more capable.

![](https://every.to/assets/icons/lock_outline-e4a08f6f075d2636d461a53f49de74197467b7ea6aa9258f33347dd880029d20.svg) Create a free account to continue reading

The Only Subscription  
You Need to  
Stay at the  
Edge of AI
--------------------------------------------------------------

The essential toolkit for those shaping the future

"This might be the best value you  
can get from an AI subscription."

\- Jay S.

 [![Mail](https://every.to/assets/paywall/app_icons/every-7ac34d1cb7bd353d6e701bb00cfc61f798250095ebdcfd12f6d5eaf84386b096.png)](https://every.to/subscribe?source=post_paywall)Every Content

 [![AI&I Podcast](https://every.to/assets/app_icons/podcasts-05879434e25ad3d087a9c019d2de90fd3620fe81a3d38cc83b8ddca4ab8edb09.png)](/podcast)AI&I Podcast

 [![Monologue](https://every.to/assets/paywall/app_icons/monologue-7095346b162f13e7f142fc9de290b9c7222a65019ec6aa04abdf32bbf2b11cd5.png)](https://monologue.to/?utm_source=every&utm_medium=banner&utm_campaign=post)Monologue

 [![Cora](https://every.to/assets/paywall/app_icons/cora-c72cf67256dfbe7d1805c701b3d1605954ba559a38cfb021d66c9b350de0a6d3.png)](https://cora.computer/?utm_source=every&utm_medium=banner&utm_campaign=post)Cora

 [![Sparkle](https://every.to/assets/paywall/app_icons/sparkle-b99bd07599520a38c908455679c83a9a1aa3738412b77a38e805c92d0dce5dd6.png)](https://makeitsparkle.co/every?utm_source=every&utm_medium=banner&utm_campaign=post)Sparkle

 [![Spiral](https://every.to/assets/paywall/app_icons/spiral-e9c1b877b492911c86921b7d2a9c70c5a2a4d845019b50a4e390999caf48a01d.png)](https://writewithspiral.com/?utm_source=every&utm_medium=banner&utm_campaign=post)Spiral

Join 100,000+ leaders, builders, and innovators

![Community members](https://every.to/assets/paywall/faces-2b72f553c10b6f8c7042928513f8254f0b1056a695678d112a1159bae5c7b86a.png)

Email address

![Email](https://every.to/assets/icons/mail_outline-47c8cc2142e2de5d007db742a4a52b036fdedd12fc25e2f14e8e40d9c3ba9d0b.svg)

Already have an account? [Sign in](https://every.to/login)

### What is included in a subscription?

Daily insights from AI pioneers + early access to powerful AI tools

![Pencil](https://every.to/assets/popup/pencil-a7e87ba5ccd69420e5fc49591bc26230cb898e9134d96573dbdc12c35f66cc92.svg) Front-row access to the future of AI

![Sparks](https://every.to/assets/popup/sparks-aad3c464581e04cfaad49e255e463ca0baf32b9403f350a2acdfa2d6a5bdc34e.svg) Bundle of AI software

Thanks for rating this post—join the conversation by commenting below.
