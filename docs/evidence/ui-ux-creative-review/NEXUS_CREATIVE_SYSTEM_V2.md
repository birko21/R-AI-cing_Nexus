# Nexus creative system v2

Date: 2026-10-15  
Status: Implemented locally; hosted visual gate pending deployment

## Creative intent

Nexus is a private racing research operating surface. It should feel precise,
quiet and observant: a control room for evidence, not a betting interface and
not a generic admin dashboard.

The redesign preserves the agreed workspace-atlas structure while giving the
shell a stronger point of view:

- a geometric Nexus mark and restrained research-OS wordmark;
- a deep navy instrument background with a measured grid and orbit motif;
- cyan for system geometry, blue for interaction, green for verified/current,
  and amber for warnings or rights boundaries;
- large editorial workspace headlines paired with compact uppercase metadata;
- evidence cards that read as instruments, with clear state, source and action
  hierarchy;
- motion used only for secure handshake/loading feedback and disabled when the
  user prefers reduced motion.

## Experience rules

1. A licensed session never renders synthetic racing content while provider
   mode is unresolved.
2. Every workspace has a meaningful destination in synthetic mode. Preview
   surfaces remain clearly labelled and do not imply live or validated output.
3. Live mode keeps the read-only capability boundary visible at the point of
   action, not only in footer text.
4. No visual treatment may make a forecast, market, selection or alert look
   like an order or wager action.
5. Provenance is part of the primary composition: receipt, revision, rights,
   freshness and limitation are never hidden behind debug affordances.
6. Responsive layouts may reflow, stack or scroll, but the active workspace and
   primary action must remain obvious at 390px, 768px and 1440px.

## Implemented in this pass

- Neutral secure-provider handshake/loading state for authenticated startup.
- Branded topbar with Nexus mark, workspace title, owner session marker and
  mode badges.
- Instrument-grid background, orbit motif, improved type scale and visual
  hierarchy.
- Control-deck filter panel, upgraded summary strip, live health panel and
  richer evidence cards.
- Workspace-specific synthetic previews for all atlas entries, rather than a
  repeated generic placeholder.
- Responsive preview grid, mobile stacking, scroll hint for the atlas, and
  reduced-motion handling.
- Existing no-wagering, provenance, Auth0, axe and keyboard behavior retained.

## Remaining gate

The design is not creatively signed off until the deployed hosted branch is
checked at desktop, tablet and mobile sizes, the licensed boot state is tested
with a real authenticated session, and the visual-owner variance register is
updated against the approved reference captures.
