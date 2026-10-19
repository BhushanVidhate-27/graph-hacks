# Heron AI Frontend Clone (`angy-fronted`)

A high-fidelity clone of [Heron AI](https://heronaiapp.com/) — the award-winning architectural CAD/BIM autonomous agent website and platform designed by Bearplus Agency.

---

## ✨ Features Replicated

1. **Aesthetic & Technical Design System**:
   - **CAD HUD Grid & Hairlines**: Precision 1px borders, dashed dividers, and authentic corner `+` crosshair markers.
   - **Live Coordinates HUD**: Real-time mouse position tracking (`X: [px] / Y: [px]`) with live system diagnostics.
   - **Signature Heron Split-Button**: Smooth sliding text and animated arrow icon hover micro-interactions.
   - **Authentic Heron Brand Assets**: Replicated 3D origami bird polygon logo mark and "HERON AI" logotype.
   - **SVG Noise Shaders**: Integrated `#sharedDisplacementFilter` with `feTurbulence` and `feDisplacementMap` for blueprint textures.

2. **Interactive CAD Violation Inspector**:
   - **"Click & Drag Your Mouse to Reveal Violations"**:
   - Interactive split-slider comparing the manual unverified model (Rev 01) with the Heron-remediated model (Rev 02).
   - Interactive pinpoints for real-world codes:
     - `IBC 1015.3` (Guardrail required for fall protection)
     - `IBC 1011.11` (Handrails required)
     - `IBC 1017.2` (Exit Access Travel Distance)
     - `ICC A117.1 §604.3.1` (Accessible Restroom 60" Turning Clearance)
   - Live "Apply Edit Automatically" action trigger.

3. **Core Website Sections**:
   - **Hero Section**: Headline, metadata HUD card, supported CAD ecosystem ticker (Revit, Rhino, ArchiCAD, SketchUp).
   - **Problems Section**: The 4 manual design bottlenecks (Manual, Disjointed, Blind, Slow).
   - **Product Showcase**: Detailed overview of `[01] Heron Chat Widget` and `[02] Heron Dashboard`.
   - **Workflow Section**: The 4-step loop (Observe, Advise, Act, Learn).
   - **Discipline Roles**: Architects, Interior Designers, BIM Managers, Drafters, Engineers, Design Leads, Small Firms.
   - **Pricing Plans**: Free ($0), Standard ($99/mo), Business ($295/mo), Enterprise (Custom) with Monthly/Yearly toggle (15% savings).
   - **FAQ Accordion**: 5 expandable technical questions with code rollback and BIM database explanations.
   - **Footer**: Bearplus agency credits, Denver/Sydney office addresses, legal navigation.

4. **Integrated Viewer & Simulation Module**:
   - Built-in bottom control bar allowing instant switching between:
     - 🌐 **Full Website View** (The full high-fidelity landing experience)
     - 💬 **In-Tool Chat Widget Simulator** (Interactive floating Revit/Rhino agent chat where you can prompt Heron to inspect models and approve proposed edits)
     - 📊 **Heron Dashboard Simulator** (Centralized cloud oversight queue with project switcher, IBC scores, and commit actions)
     - 📱 **Responsive Viewport Frame** (Interactive device preview in Desktop 1440px, iPad 820px, and iPhone 390px frames with internal scrolling)

---

## 🚀 Quick Start

### 1. Development Server
```bash
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

### 2. Production Build
```bash
npm run build
```
Build output is generated into the `dist/` directory.

### 3. Preview Production Build
```bash
npm run preview
```
Open [http://localhost:4173](http://localhost:4173).
