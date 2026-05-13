# Brains

Brains are a lightweight behavior tree system used by {{ab.m}} labels.

In practice, a brain:

- picks one or more labels to run every tick
- interprets each label result as success or fail
- combines child results with selector or sequence rules
- stores useful blackboard-style values in agent inventory

If you are familiar with behavior trees:

- SEL is a selector (first child success wins)
- SEQ is a sequence (all children must succeed)
- a normal label is a leaf node


## Mental model

Each agent can have one root brain object in inventory key __BRAIN__.

The root is usually a selector:

- SEL root
	- child 1 (leaf or composite)
	- child 2 (leaf or composite)
	- ...

Each tick:

1. The brain system visits every agent that has __BRAIN__.
2. The root brain runs.
3. Composite nodes execute children.
4. Leaf nodes execute a {{ab.m}} label and return a poll result.

Brains do not have a permanent done state. They are evaluated repeatedly.


## How results drive behavior

Brains use success/fail-style outcomes:

- PollResults.BT_SUCCESS
- PollResults.BT_FAIL
- PollResults.OK_IDLE (used as reset/neutral state internally)

Composite behavior:

- Selector (SEL):
	- starts as fail
	- runs children in order
	- first child that succeeds makes selector succeed
	- if none succeed, selector fails
- Sequence (SEQ):
	- runs children in order
	- first child that fails makes sequence fail
	- if all succeed, sequence succeeds

### Result modifiers

The runtime also supports modifier flags on a brain node:

- Invert
- AlwayFail
- AlwaySuccess

These flags alter the final node result after execution.


## Leaf label execution rules

A simple brain node points at one major label.

When a leaf runs:

1. On first run only, if sub label enter exists, it is executed once.
2. If sub label test exists, that sub label is executed for result.
3. Otherwise, execution starts at location 0 of the major label.

Runtime variables injected for the label task:

- BRAIN: current brain object
- BRAIN_AGENT: object form of the agent id
- BRAIN_AGENT_ID: raw agent id

This is why most brain labels read/write inventory through BRAIN_AGENT.


## Defining brains declaratively

Brains can be assembled from Python-friendly structures.

Supported structures:

- string: label name
- MastNode: direct label node
- list: add each item as child
- dict:
	- single key starting with SEL -> selector composite
	- single key starting with SEQ -> sequence composite
	- otherwise use keys label and data

Common pattern:

```yaml
brain:
	SEQ:
		- ai_fleet_init_blackboard
		- SEL:
			- ai_fleet_chase_best_anger
			- label: ai_fleet_chase_roles
				data:
					test_roles: station
			- label: ai_fleet_chase_roles
				data:
					test_roles: __player__
		- ai_fleet_calc_forward_vector
		- ai_fleet_scatter_formation
```

Notes:

- Child order matters for SEL and SEQ.
- data on a node is passed into the task context for that label.
- metadata defaults in the label and runtime data overrides are often used together.


## Quick start: attach a brain

Brains are typically attached from Python when spawning/configuring an NPC or fleet controller.

```py
from sbs_utils.procedural.brain import brain_add

brain_add(
	agent_id,
	{
		"SEQ main": [
			"ai_fleet_init_blackboard",
			{
				"SEL choose_target": [
					"ai_fleet_chase_best_anger",
					{"label": "ai_fleet_chase_roles", "data": {"test_roles": "station"}},
					{"label": "ai_fleet_chase_roles", "data": {"test_roles": "__player__"}},
				]
			},
			"ai_fleet_calc_forward_vector",
			"ai_fleet_scatter_formation",
		]
	},
	client_id=0,
)
```

The first call creates a default selector root if needed, then inserts your tree.


## Metadata and per-node data

A brain label often declares defaults in metadata.

Example:

```mast
=== ai_fleet_chase_roles
metadata: yaml
	type: brain/npc
	use_arena: True
	test_roles: station
	exclude_roles: raider
		...
```

Then a brain node can provide data overrides:

```yaml
label: ai_fleet_chase_roles
data:
	test_roles: __player__
```

This allows one label to be reused with different behavior.


## Active brain status text

The runtime tracks active text for debugging/UI use.

For a leaf node:

- active: label name
- active_desc:
	- desc inventory value if present
	- optionally random choice if desc is a list
	- then DisplayName inventory value if present
	- otherwise label name

For a selector, when one child succeeds:

- that child becomes active
- brain_active inventory is set to child active_desc


## Worked example: fleet brain

Using your fleet script shape:

1. ai_fleet_init_blackboard
	- resets target data
	- computes lead ship and local arena
2. SEL target choice
	- try ai_fleet_chase_best_anger first
	- if that fails, try role-based targeting variants
3. ai_fleet_calc_forward_vector
	- computes destination and throttle
4. ai_fleet_scatter_formation
	- issues per-ship target positions

This creates robust fallback logic:

- preferred tactical behavior first
- deterministic fallbacks second
- movement only after a valid target exists


## Minimal authoring checklist

When writing a new brain label:

1. Add metadata defaults for tunables (distance, roles, stop_dist, etc.).
2. Use BRAIN_AGENT inventory as your blackboard.
3. Return early with yield fail when prerequisites are missing.
4. Set outputs (target, target_position, throttle, etc.).
5. End with yield success.

When composing a tree:

1. Use SEQ for required steps.
2. Use SEL for fallback options.
3. Put cheap/high-confidence options earlier.
4. Keep each label focused on one responsibility.


## Debugging tips

- If a brain seems idle, verify the agent has __BRAIN__ assigned.
- If a label never runs, confirm the label name resolves correctly.
- If selector never succeeds, inspect each child for missing prerequisites.
- If targeting stalls, verify blackboard keys are populated in init step.
- Track brain_active to see which child is currently winning selection.


## API touchpoints

Core procedural calls:

- brain_add(...)
- brain_clear(...)
- brains_run_all(...)

These are defined in:

- sbs_utils/procedural/brain.py

Example mission labels:

- fleets/brain_fleet.mast

Together they provide a full pattern for authoring reusable NPC decision logic.
