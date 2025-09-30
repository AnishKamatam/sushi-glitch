# Leviathan Overview

## Vision

- **Tagline:** Bringing big insights for small crews
- **Mission:** Deliver a single phone-based copilot that improves planning, in-trip sonar timing, and on-deck handling to raise income without extra hardware or crew.

## Problem Landscape

- Small and solo skippers juggle three hard-to-optimize decisions: trip planning, reacting to sonar cues, and preserving catch freshness.
- Reliance on heuristics, fragmented toolchains, and poor connectivity causes missed bite windows, inefficient drops, and inconsistent bleeding or icing.
- Volatile yields and auction prices directly impact livelihoods; a unified assistant can stabilize outcomes.

## Target Users

- Small-boat operators and solo skippers who manage end-to-end trips.
- Operate with phones on deck, limited/no internet offshore, wet or gloved hands, and short attention spans.
- Require support for three workflows: where/when to fish, how to act on sonar, and how to handle catch for grade and price.

## Solution Pillars

### 1. Pre-Departure Planner

- Aggregates marine weather, tides, currents, and lunar data.
- Outputs a Plan Card with target species, depth band, time window, area hints, fuel notes, safety notes, and Plan B.

### 2. At-Sea Sonar Assist with TTS

- Ingests sonar screenshots/logs from common units or portable bobbers.
- Produces concise cues (drop/move) and reads them aloud via text-to-speech.

### 3. Offline Freshness & Processing QA

- Uses on-device vision to score bleeding, ice contact, and bruising.
- Returns a handling score, confidence, and one recommended next action.
- Works offline; cloud services optional in port.

## Differentiation

- Unified app covering planning, execution, and handling reduces context switching.
- Phone-first, offline-first experience; no boat Wi-Fi or new hardware required.
- Sonar-aware prompts with TTS, expanding beyond typical chart/weather tools.
- Quick time-to-value: accepts screenshots/logs, enabling immediate trials.
- Expandable moat via NMEA integration, species-specific playbooks, and market-aware offloading timing.

## Data Flywheel & Feedback Loop

- Each trip (with user permission) contributes anonymized data that improves predictive models.
- Logged skipper actions—even when diverging from guidance—capture expert intuition as training signals.

## Key Performance Indicators

- **Primary MVP KPI:** Auction price premium via improved freshness/handling (proxy: uplift in on-device freshness score across a trip).
- **Secondary KPIs:** Catch per unit effort, fuel/time per kg landed, handling defect rate, planner adherence.
- Measurement pairs logged scores/timestamps with before–after comparisons; weights refined after early user feedback.

## MVP Scope

- Region/species: Generic coastal scenario with one or two common species and a representative gear example.
- **Planner:** Ingest public marine signals, output Plan Card with target window, depth band, area hint, and Plan B.
- **Sonar Assist:** Accept image/log, estimate school depth & density, speak a maneuver cue.
- **Freshness QA:** Phone camera view, deliver indicators plus one next action.

## Architecture Snapshot

- **Phone App UI:** Tabs for Plan Card, Sonar Assist, Freshness QA.
- **On-Device Models:** Small VLM for freshness; heuristic/compact ML for sonar cues; native TTS.
- **Offline Store:** Trip → Haul → Event log with images, scores, and timestamps.
- **Optional Cloud (port-only):** Aggregates planning inputs and returns compact plan JSON; not required mid-trip.
- **Data Flow:** Inputs (marine signals, sonar frames, camera) → Models → Guidance (spoken + visual) → Local KPI logging → Optional sync in port.

## Platform Strategy

- Android-first implementation; iOS planned later.
- Phone is the sole required device.

## Data Plan

- **Planning Inputs:** Public marine weather, tide, current, lunar sources; MVP mocks/caches representative slices.
- **Sonar Inputs:** Screenshots/logs from popular units or portable bobbers; MVP uses curated library with annotations (depth band, density, school width).
- **Freshness Inputs:** Open fish image sets plus small onboard sample; candidate models include compact Gemma or Qwen variants distilled for mobile.

## Risk Matrix & Mitigations

- **Sonar Variance:** Start with screenshot/log ingest; later expand via NMEA/vendor SDKs.
- **On-Device Model Accuracy:** Narrow tasks, surface confidence, allow manual overrides.
- **Usability in Wet/Motion Environments:** TTS-first flows, large buttons, offline resilience.
- **Regulatory Differences:** MVP excludes quotas/closures; future work adds region-specific guidance.
- **Crowding (Honey Pot):** Provide multiple viable areas instead of a single spot.

## Two-Week Development Roadmap

| Day | Milestone               | Features                                                                                                                 | Model/Data Work                                                         | Demo Artifact                           | Owner |
| --- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- | --------------------------------------- | ----- |
| 0   | Scope lock              | Android shell app with three tabs, Plan Card stub, baseline TTS                                                          | Collect 10–20 sonar frames, 20–30 deck photos; define annotation schema | Clickable flow video                    | Team  |
| 7   | End-to-end path working | Planner from mocked inputs; Sonar Assist with depth cue; Freshness QA v0 with three levels + next action; local trip log | Small distilled on-device QA model; heuristic sonar cue                 | Screen recording of happy path on phone | Team  |
| 12  | Polished demo           | Enhanced Plan Card with Plan B; refined freshness rubric & confidence; metrics overlay with score deltas                 | Curated demo set; optional light finetune on collected photos           | Live phone demo + final video clip      | Team  |
