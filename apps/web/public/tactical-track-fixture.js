window.NEXUS_TACTICAL_FIXTURE = {
  schemaVersion: 'nexus.tactical-track.fixture.v1',
  source: {
    kind: 'synthetic',
    id: 'synthetic://betfair/mock-v1',
    live: false,
    providerActivated: false
  },
  race: {
    meeting: 'Randwick',
    race: 'R3',
    code: 'THOROUGHBRED',
    distanceMeters: 1200,
    view: 'EARLY_SETTLING_0_400M'
  },
  entries: [
    {number: 1, name: 'Coastal Strike', color: '#35e2a0', group: 'LEAD', detail: 'High early speed · likely to cross over early', factor: 'Draw advantage · Barrier 3', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/emerald-gold.png', label: 'Emerald and gold', primary: '#35e2a0', secondary: '#d9ac3a', pattern: 'solid'}},
    {number: 2, name: 'Northern Legend', color: '#35e2a0', group: 'LEAD', detail: 'Tracks the speed and settles just off the rail', factor: 'Consistent early profile', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/navy-cyan.png', label: 'Navy and cyan', primary: '#153b62', secondary: '#58d2ef', pattern: 'solid'}},
    {number: 3, name: 'Maple Ridge', color: '#f0b638', group: 'ON PACE', detail: 'Contesting the first line in the scenario', factor: 'Forward intent · synthetic', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/crimson-ivory.png', label: 'Crimson and ivory', primary: '#a8323d', secondary: '#f3e4c7', pattern: 'solid'}},
    {number: 4, name: 'Ocean Circuit', color: '#78b9ef', group: 'MIDFIELD', detail: 'Settles behind the first pair', factor: 'Balanced fictional profile', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/navy-cyan.png', label: 'Navy and cyan', primary: '#153b62', secondary: '#58d2ef', pattern: 'solid'}},
    {number: 5, name: 'Desert King', color: '#f0b638', group: 'ON PACE', detail: 'Shares the contested lead band', factor: 'Distance fit · illustrative', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/crimson-ivory.png', label: 'Crimson and ivory', primary: '#a8323d', secondary: '#f3e4c7', pattern: 'solid'}},
    {number: 6, name: 'Royal Avenue', color: '#78b9ef', group: 'MIDFIELD', detail: 'Midfield runner with room to improve', factor: 'Pace map only', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/emerald-gold.png', label: 'Emerald and gold', primary: '#35e2a0', secondary: '#d9ac3a', pattern: 'solid'}},
    {number: 7, name: 'Eagle Farm', color: '#fb4b78', group: 'BACKMARKERS', detail: 'Settles toward the rear of the field', factor: 'Backmarker band', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/crimson-ivory.png', label: 'Crimson and ivory', primary: '#a8323d', secondary: '#f3e4c7', pattern: 'solid'}},
    {number: 8, name: 'Doodmen', color: '#fb4b78', group: 'BACKMARKERS', detail: 'Rear group · no precise trajectory claimed', factor: 'Synthetic fixture', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/navy-cyan.png', label: 'Navy and cyan', primary: '#153b62', secondary: '#58d2ef', pattern: 'solid'}},
    {number: 9, name: 'Rising Sun', color: '#fb4b78', group: 'BACKMARKERS', detail: 'Rear group · no precise trajectory claimed', factor: 'Synthetic fixture', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/emerald-gold.png', label: 'Emerald and gold', primary: '#35e2a0', secondary: '#d9ac3a', pattern: 'solid'}},
    {number: 10, name: 'Midnight Storm', color: '#78b9ef', group: 'MIDFIELD', detail: 'Midfield settling band', factor: 'Synthetic fixture', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/navy-cyan.png', label: 'Navy and cyan', primary: '#153b62', secondary: '#58d2ef', pattern: 'solid'}},
    {number: 11, name: 'Silver Vale', color: '#fb4b78', group: 'BACKMARKERS', detail: 'Rear group · no precise trajectory claimed', factor: 'Synthetic fixture', silks: {source: 'synthetic-local', asset: 'tactical-track-runners/crimson-ivory.png', label: 'Crimson and ivory', primary: '#a8323d', secondary: '#f3e4c7', pattern: 'solid'}}
  ],
  scenarios: {
    base: {positions: {1: [78, 60, 1], 2: [73, 69, 1], 3: [67, 58, 1], 5: [63, 72, 1], 4: [55, 61, 1], 6: [52, 72, 1], 10: [47, 67, 1], 7: [36, 59, 1], 8: [30, 72, 1], 9: [25, 67, 1], 11: [20, 77, 1]}},
    contested: {positions: {1: [82, 58, 1], 2: [74, 69, 1], 3: [76, 73, 1], 5: [70, 58, 1], 4: [58, 64, 1], 6: [53, 73, 1], 10: [47, 70, 1], 7: [34, 61, 1], 8: [28, 74, 1], 9: [23, 68, 1], 11: [18, 77, 1]}}
  }
};
