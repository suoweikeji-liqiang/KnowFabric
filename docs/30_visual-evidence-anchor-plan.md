# Visual Evidence Anchor Plan

> Status: planning note
> Date: 2026-05-07
> Scope: future multimodal evidence support for HVAC manuals and standards

## Why This Exists

KnowFabric already treats text chunks as the retrieval truth source for text
knowledge objects. HVAC manuals also contain high-value visual evidence that
does not reduce cleanly to OCR text:

- wiring diagrams
- terminal block drawings
- control board layouts
- controller screen captures
- nameplates
- parameter tables rendered as images
- system schematics and piping diagrams
- fault flowcharts
- equipment structure diagrams

This document records the intended direction so future work does not treat the
visual pipeline as "OCR only".

## Core Decision

Visual evidence is a first-class evidence anchor, parallel to text chunks.

Do not force all page images through OCR and then pretend the OCR text is the
only source of truth. OCR is useful for tables, labels, and nameplates, but
diagrams often require visual semantic interpretation: components, terminals,
signals, connections, and spatial relationships.

The intended evidence model is:

```text
Document
  -> Page
     -> Text chunks
        -> text evidence anchors
     -> Visual regions
        -> OCR text when useful
        -> visual semantic caption
        -> visual entities and relationships
        -> image evidence anchors
```

Text chunks remain the source of truth for text-derived facts. Visual regions
become the source of truth for image-derived facts.

## Visual Evidence Types

### 1. Text-like visual evidence

Examples:

- scanned fault-code tables
- parameter tables
- nameplates
- controller menu screens with readable labels

Primary method:

- OCR or page transcription first
- then normal text-based extraction and anchoring

Expected outputs:

- `ocr_text`
- table rows if structure is recoverable
- page or region image anchor

### 2. Diagram-like visual evidence

Examples:

- wiring diagrams
- terminal block maps
- electrical schematics
- piping and system diagrams
- control logic flowcharts

Primary method:

- visual-language model semantic labeling
- entity and relationship extraction where confidence is high
- preserve region image as evidence even when structured extraction is partial

Expected outputs:

- image type
- caption or semantic summary
- entities such as terminals, sensors, relays, pumps, valves, controllers
- relationships such as connected-to, signal-input-to, ground-reference,
  upstream-of, downstream-of, controls, measures
- page and bounding box evidence

### 3. Mixed visual evidence

Examples:

- controller UI pages
- BMS point list screenshots
- annotated equipment photos
- diagrams with embedded tables

Primary method:

- OCR plus visual semantic labeling
- extract only facts supported by the visible region
- keep uncertain structure as caption evidence rather than over-structured facts

## Example Wiring Diagram Output

```json
{
  "image_type": "wiring_diagram",
  "page_no": 42,
  "summary": "Control board terminal J2 provides external chilled water setpoint input; J2-2 through J2-6 are shown as signal and ground reference terminals.",
  "entities": [
    {"type": "terminal", "label": "J2-2"},
    {"type": "terminal", "label": "J2-6"},
    {"type": "signal", "label": "External Chilled Water Setpoint"},
    {"type": "ground", "label": "GND"}
  ],
  "relationships": [
    {
      "from": "External Chilled Water Setpoint",
      "to": "J2-2",
      "relation": "input_signal_connected_to_terminal"
    },
    {
      "from": "J2-6",
      "to": "GND",
      "relation": "terminal_ground_reference"
    }
  ],
  "evidence_image": {
    "page_image": "pages/page_042.png",
    "bbox": [120, 340, 820, 910]
  }
}
```

This is intentionally different from OCR output. The knowledge value is the
relationship between labels and graphical elements, not just the visible text.

## Candidate Data Model

These names are provisional. They should be introduced through migrations only
when implementation starts.

### `document_page_image`

Purpose: store rendered page images or detected regions.

Suggested fields:

- `page_image_id`
- `doc_id`
- `page_id`
- `page_no`
- `image_path`
- `bbox`
- `image_type`
- `caption`
- `ocr_text`
- `vl_summary`
- `vl_model`
- `confidence`
- `created_at`

### `visual_evidence_anchor`

Purpose: attach a knowledge object to a visual region.

Suggested fields:

- `visual_evidence_id`
- `knowledge_object_id`
- `page_image_id`
- `doc_id`
- `page_no`
- `bbox`
- `evidence_role`
- `evidence_caption`
- `extracted_entities_json`
- `extracted_relationships_json`
- `model_used`
- `confidence`

## Retrieval Behavior

When a consumer asks for knowledge, KnowFabric should be able to return mixed
evidence:

- text evidence from chunks
- visual evidence from page regions
- citation with page number and region
- optional rendered page preview or image path

Example answer behavior:

```text
The external chilled water setpoint input is shown on the control board wiring
diagram. Text evidence is on page 45, and the wiring evidence is on page 46,
region `bbox=[...]`, where terminal J2-2 is labeled as the input and J2-6 as
ground reference.
```

The API should not hide visual evidence behind OCR text. If a fact is supported
by a diagram, the response should identify the diagram/page/region explicitly.

## Production Strategy

### Model Role Decision

The text-first knowledge extraction mainline should stay on long-context text
models such as DeepSeek V4/V4 Pro. In the 2026-05-07 five-document OEM
comparison run, MiMo V2.5 Pro was useful but less stable for text-only
document-level extraction: it produced good results on several short manuals,
but timed out on a 111-page fault-code manual and was not consistently better
than DeepSeek for text evidence anchoring.

MiMo should therefore be treated primarily as a candidate visual-semantic
model, not as the main OCR or text extraction engine. Its value is likely in
whole-page or region-level multimodal understanding: wiring diagrams, system
schematics, controller screen captures, nameplates, terminal maps, and mixed
table/diagram pages. OCR remains a tool for text-like visual evidence, but
diagram interpretation should be evaluated as visual semantic labeling with
page/bounding-box anchors.

### Phase 1: Triage visual pages

Input:

- PDFs already marked `low_or_no_text`
- table-heavy or diagram-heavy manuals from the source inventory

Output:

- page-level visual manifest
- page image paths
- coarse page type:
  - text_scan
  - parameter_table
  - fault_table
  - wiring_diagram
  - system_schematic
  - controller_screen
  - nameplate
  - equipment_structure
  - other

### Phase 2: Small closed-loop validation

Run against 3-5 high-value image-heavy manuals:

- render pages
- classify visual regions
- run OCR only where OCR is appropriate
- run VL semantic labeling for diagrams
- produce candidate visual evidence anchors
- manually review 20-50 examples

Success criteria:

- the model distinguishes tables from wiring diagrams
- evidence points to page and region, not just a loose document citation
- wiring/control facts are not invented from labels alone
- uncertain diagrams remain captions, not overconfident structured facts

### Phase 3: Integrate with KO review and retrieval

Add visual evidence to review packs and API responses:

- reviewer can see page image or cropped region
- accepted KO can carry text evidence, visual evidence, or both
- downstream consumers can cite diagram evidence

## Guardrails

- Do not treat OCR as sufficient for wiring diagrams.
- Do not create structured wiring relationships unless the visual relation is
  clearly visible.
- Keep low-confidence diagram interpretation as caption evidence.
- Preserve page number and bounding box for every visual claim.
- Keep visual evidence parallel to text chunks; do not replace chunk evidence.
- Do not mix product catalog imagery into operational knowledge extraction
  without an explicit performance/application profile.

## Relationship To Existing Work

Existing scripts under `scripts/run_local_multimodal_validation.py`,
`scripts/run_remote_mimo_ocr_validation.py`, and related OCR text validation
scripts are useful experiments, but they are not yet the production visual
evidence pipeline.

The next production step is not "OCR all images". It is visual page triage plus
evidence anchoring.
