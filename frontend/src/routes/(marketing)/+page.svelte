<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const plans = [
		{
			name: 'Free',
			key: 'free',
			price: 0,
			features: ['5 sessions/month', '3 draft angles', 'Style preferences'],
			cta: 'Start Free',
			href: '/register',
			highlighted: false
		},
		{
			name: 'Pro',
			key: 'pro',
			price: 19,
			features: ['Unlimited sessions', 'Voice input', 'Advanced style learning', 'Priority AI'],
			cta: 'Coming Soon',
			href: undefined,
			highlighted: true
		},
		{
			name: 'Team',
			key: 'team',
			price: 49,
			features: ['Everything in Pro', '5 team members', 'Shared styles', 'Admin dashboard'],
			cta: 'Coming Soon',
			href: undefined,
			highlighted: false
		}
	];

	const steps = [
		{ num: '1', title: 'Describe', desc: 'Tell Inkwell what you want to write — essay, newsletter, review, anything.' },
		{ num: '2', title: 'Interview', desc: 'AI asks targeted questions to draw out your real stories and insights.' },
		{ num: '3', title: 'Choose', desc: 'Compare 3 draft angles side-by-side and highlight what resonates.' },
		{ num: '4', title: 'Refine', desc: 'Inkwell synthesizes your favorites into a polished draft you can keep refining.' }
	];

	const features = [
		{ title: 'AI Interview', desc: 'Targeted questions extract your real stories, experiences, and insights — so your writing sounds like you, not a chatbot.' },
		{ title: '3 Draft Angles', desc: 'Every round generates 3 distinct approaches. Highlight your favorites across all three to guide the next round.' },
		{ title: 'Style Learning', desc: 'Upload writing samples, set preferences, accept or reject suggestions — Inkwell learns your voice over time.' },
		{ title: 'Voice Input', desc: 'Speak your answers naturally. Inkwell transcribes and weaves your spoken words into the writing.' }
	];
</script>

<svelte:head>
	<title>Inkwell — AI Writing Partner</title>
	<meta name="description" content="Your AI writing partner that learns your voice. Describe, interview, compare angles, and refine — all powered by AI that compounds with every session." />
</svelte:head>

<!-- Hero -->
<section class="hero">
	<div class="hero-inner">
		<h1>Your AI writing partner<br />that learns your voice</h1>
		<p class="hero-sub">
			Describe what you want to write. Inkwell interviews you, generates 3 draft angles,
			and refines based on what you highlight — getting better with every session.
		</p>
		{#if data.user}
			<a href="/dashboard" class="btn-primary">Go to Dashboard</a>
		{:else}
			<a href="/register" class="btn-primary">Start Writing Free</a>
		{/if}
	</div>
</section>

<!-- How It Works -->
<section class="section" id="features">
	<h2 class="section-title">How it works</h2>
	<div class="steps-grid">
		{#each steps as step}
			<div class="step-card">
				<span class="step-num">{step.num}</span>
				<h3>{step.title}</h3>
				<p>{step.desc}</p>
			</div>
		{/each}
	</div>
</section>

<!-- Features -->
<section class="section section-alt">
	<h2 class="section-title">Built for real writers</h2>
	<div class="features-grid">
		{#each features as feature}
			<div class="feature-card">
				<h3>{feature.title}</h3>
				<p>{feature.desc}</p>
			</div>
		{/each}
	</div>
</section>

<!-- Pricing -->
<section class="section" id="pricing">
	<h2 class="section-title">Simple pricing</h2>
	<p class="section-sub">Start free. Upgrade when you're ready.</p>
	<div class="pricing-grid">
		{#each plans as plan}
			<div class="pricing-card" class:highlighted={plan.highlighted}>
				{#if plan.highlighted}
					<span class="badge">Popular</span>
				{/if}
				<h3>{plan.name}</h3>
				<div class="price">
					{#if plan.price === 0}
						<span class="amount">Free</span>
					{:else}
						<span class="amount">${plan.price}</span>
						<span class="period">/mo</span>
					{/if}
				</div>
				<ul>
					{#each plan.features as feature}
						<li>{feature}</li>
					{/each}
				</ul>
				{#if plan.href}
					<a href={plan.href} class="btn-plan">{plan.cta}</a>
				{:else}
					<button class="btn-plan btn-disabled" disabled>{plan.cta}</button>
				{/if}
			</div>
		{/each}
	</div>
</section>

<!-- Final CTA -->
<section class="section cta-section">
	<h2>Ready to write something great?</h2>
	<p>Join writers who use Inkwell to find their voice and finish what they start.</p>
	{#if data.user}
		<a href="/dashboard" class="btn-primary">Go to Dashboard</a>
	{:else}
		<a href="/register" class="btn-primary">Create Free Account</a>
	{/if}
</section>

<style>
	/* Hero */
	.hero {
		padding: 100px 40px 80px;
		text-align: center;
	}

	.hero-inner {
		max-width: 680px;
		margin: 0 auto;
	}

	.hero h1 {
		font-family: 'Newsreader', serif;
		font-weight: 600;
		font-size: 48px;
		line-height: 1.15;
		letter-spacing: -0.02em;
		margin: 0 0 20px;
		color: var(--chrome-text);
	}

	.hero-sub {
		font-size: 17px;
		line-height: 1.6;
		color: var(--chrome-text-muted);
		margin: 0 0 36px;
		max-width: 520px;
		margin-left: auto;
		margin-right: auto;
	}

	.btn-primary {
		display: inline-block;
		background: var(--accent);
		color: white;
		padding: 14px 36px;
		border-radius: 28px;
		font-size: 16px;
		font-weight: 600;
		text-decoration: none;
		transition: opacity 0.2s;
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	/* Sections */
	.section {
		padding: 80px 40px;
		max-width: 1080px;
		margin: 0 auto;
	}

	.section-alt {
		background: var(--chrome-surface);
		max-width: none;
		padding-left: 40px;
		padding-right: 40px;
	}

	.section-alt > * {
		max-width: 1080px;
		margin-left: auto;
		margin-right: auto;
	}

	.section-title {
		font-family: 'Newsreader', serif;
		font-weight: 600;
		font-size: 32px;
		text-align: center;
		margin: 0 0 12px;
		color: var(--chrome-text);
	}

	.section-sub {
		text-align: center;
		color: var(--chrome-text-muted);
		font-size: 15px;
		margin: 0 0 48px;
	}

	/* Steps */
	.steps-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 24px;
		margin-top: 48px;
	}

	.step-card {
		padding: 28px 24px;
		border-radius: 12px;
		border: 1px solid var(--chrome-border);
		background: var(--chrome-surface);
	}

	.step-num {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		background: var(--accent);
		color: white;
		font-weight: 700;
		font-size: 14px;
		margin-bottom: 16px;
	}

	.step-card h3 {
		font-size: 17px;
		font-weight: 600;
		margin: 0 0 8px;
		color: var(--chrome-text);
	}

	.step-card p {
		font-size: 14px;
		line-height: 1.5;
		color: var(--chrome-text-muted);
		margin: 0;
	}

	/* Features */
	.features-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 24px;
		margin-top: 48px;
	}

	.feature-card {
		padding: 28px 24px;
		border-radius: 12px;
		border: 1px solid var(--chrome-border);
		background: var(--chrome);
	}

	.feature-card h3 {
		font-size: 17px;
		font-weight: 600;
		margin: 0 0 8px;
		color: var(--chrome-text);
	}

	.feature-card p {
		font-size: 14px;
		line-height: 1.6;
		color: var(--chrome-text-muted);
		margin: 0;
	}

	/* Pricing */
	.pricing-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 24px;
		margin-top: 48px;
	}

	.pricing-card {
		padding: 32px 28px;
		border-radius: 12px;
		border: 1px solid var(--chrome-border);
		background: var(--chrome-surface);
		display: flex;
		flex-direction: column;
		position: relative;
	}

	.pricing-card.highlighted {
		border-color: var(--accent);
		box-shadow: 0 0 0 1px var(--accent);
	}

	.badge {
		position: absolute;
		top: -10px;
		left: 50%;
		transform: translateX(-50%);
		background: var(--accent);
		color: white;
		font-size: 11px;
		font-weight: 700;
		padding: 3px 14px;
		border-radius: 12px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.pricing-card h3 {
		font-size: 18px;
		font-weight: 600;
		margin: 0 0 8px;
		color: var(--chrome-text);
	}

	.price {
		margin-bottom: 20px;
	}

	.amount {
		font-family: 'Newsreader', serif;
		font-size: 36px;
		font-weight: 600;
		color: var(--chrome-text);
	}

	.period {
		font-size: 14px;
		color: var(--chrome-text-muted);
	}

	.pricing-card ul {
		list-style: none;
		padding: 0;
		margin: 0 0 24px;
		flex: 1;
	}

	.pricing-card li {
		font-size: 14px;
		color: var(--chrome-text-muted);
		padding: 6px 0;
		border-bottom: 1px solid var(--chrome-border);
	}

	.pricing-card li:last-child {
		border-bottom: none;
	}

	.btn-plan {
		display: block;
		text-align: center;
		padding: 12px;
		border-radius: 8px;
		border: 1px solid var(--accent);
		background: transparent;
		color: var(--accent);
		font-size: 14px;
		font-weight: 600;
		font-family: inherit;
		text-decoration: none;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-plan:hover {
		background: var(--accent);
		color: white;
	}

	.btn-disabled {
		border-color: var(--chrome-border);
		color: var(--chrome-text-muted);
		cursor: not-allowed;
	}

	.btn-disabled:hover {
		background: transparent;
		color: var(--chrome-text-muted);
	}

	/* Final CTA */
	.cta-section {
		text-align: center;
		padding: 100px 40px;
	}

	.cta-section h2 {
		font-family: 'Newsreader', serif;
		font-weight: 600;
		font-size: 36px;
		margin: 0 0 12px;
		color: var(--chrome-text);
	}

	.cta-section p {
		color: var(--chrome-text-muted);
		font-size: 16px;
		margin: 0 0 32px;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.hero h1 {
			font-size: 32px;
		}

		.steps-grid {
			grid-template-columns: repeat(2, 1fr);
		}

		.features-grid {
			grid-template-columns: 1fr;
		}

		.pricing-grid {
			grid-template-columns: 1fr;
			max-width: 400px;
			margin-left: auto;
			margin-right: auto;
		}
	}

	@media (max-width: 480px) {
		.steps-grid {
			grid-template-columns: 1fr;
		}

		.hero {
			padding: 60px 20px 60px;
		}

		.section {
			padding: 60px 20px;
		}
	}
</style>
