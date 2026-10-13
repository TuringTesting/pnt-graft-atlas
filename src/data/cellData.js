/**
 * cellData.js — the content layer.
 *
 * Every key is a mesh ID. A mesh in the .glb is matched to an entry by
 * (in priority order):
 *   1. mesh.userData.id  — a Blender custom property named "id", exported with
 *                          "Include > Custom Properties" checked (recommended)
 *   2. mesh.name         — exact match, or a prefix match so that
 *                          "repair_schwann_cell_014" resolves to "repair_schwann_cell"
 * The resolver also walks up parent nodes, so you can tag a parent Empty once
 * and every child mesh inherits its ID.
 *
 * NOTHING in the rendering code knows about these entries. To add a structure:
 * add an entry here and give the mesh a matching id/name. To add a new kind of
 * content (e.g. a video, a gene-expression plot), add a field here and register
 * a section in src/components/panel/sections.jsx.
 *
 * All descriptions and references below are PLACEHOLDERS for layout — replace
 * them with your own text and DOIs. Paper URLs point at PubMed searches so they
 * always resolve; swap in https://doi.org/... links when you have them.
 */

const pubmed = (query) =>
  `https://pubmed.ncbi.nlm.nih.gov/?term=${encodeURIComponent(query)}`;

/**
 * Entry schema (all fields except `title` are optional):
 *
 * {
 *   title:       string
 *   category:    'graft' | 'host' | 'interface'   — groups the structure index
 *   color:       hex string                        — swatch in the UI + placeholder scene
 *   pickPriority:'background'                      — context volumes (e.g. the tissue
 *                                                   block) that shouldn't steal clicks
 *                                                   from cells inside them
 *   summary:     string                            — one-line lede
 *   description: string[]                          — paragraphs
 *   markers:     { name, note? }[]                 — IHC / COMET / Xenium markers
 *   papers:      { title, authors?, year?, journal?, url }[]
 *   assets: {
 *     circuitDiagramUrl: string | null             — image/SVG path, e.g. '/assets/da_circuit.svg'
 *     images: { src, caption? }[]
 *     videos: { src, caption? }[]
 *   }
 *   customPanel: string | null                     — key into src/panels/index.js for a
 *                                                   fully custom React component
 *   camera: { distanceScale?: number }             — per-structure zoom tuning
 * }
 */

export const cellData = {
  substantia_nigra: {
    title: 'Substantia Nigra (host tissue)',
    category: 'host',
    color: '#7c9ebf',
    pickPriority: 'background',
    summary: 'Midbrain nucleus receiving the graft; site of dopaminergic neuron loss in PD.',
    description: [
      'Placeholder. Describe the SN pars compacta / pars reticulata context, the implantation trajectory, and how the tissue block in this model was sampled.',
    ],
    markers: [{ name: 'TH' }, { name: 'Neuromelanin', note: 'pigment' }],
    papers: [
      {
        title: 'Peripheral nerve grafts implanted into the substantia nigra in Parkinson disease during DBS surgery',
        authors: 'van Horne CG, et al.',
        journal: 'J Neurosurg',
        url: pubmed('van Horne peripheral nerve graft substantia nigra Parkinson deep brain stimulation'),
      },
    ],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: 'nigrostriatal',
    camera: { distanceScale: 1.1 },
  },

  pnt_graft: {
    title: 'Autologous Peripheral Nerve Tissue Graft',
    category: 'graft',
    color: '#8baab8',
    pickPriority: 'background',
    summary: 'Segment of the patient’s own sural nerve implanted into the SN at the time of DBS surgery.',
    description: [
      'Placeholder. Summarize harvest, preparation, implantation, and the rationale that injured peripheral nerve provides a pro-regenerative, trophic milieu.',
      'Add your postmortem findings here: graft survival, integration at the host interface, and cellular composition over time.',
    ],
    markers: [{ name: 'S100B' }, { name: 'SOX10' }, { name: 'Collagen IV' }],
    papers: [
      {
        title: 'Autologous peripheral nerve tissue grafts in Parkinson’s disease (search)',
        url: pubmed('autologous peripheral nerve tissue graft Parkinson substantia nigra'),
      },
    ],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  repair_schwann_cell: {
    title: 'Repair Schwann Cell',
    category: 'graft',
    color: '#f9c579',
    summary: 'Schwann cells reprogrammed after nerve injury into a pro-regenerative, trophic phenotype.',
    description: [
      'Placeholder. After injury, Schwann cells dedifferentiate, upregulate c-Jun, secrete neurotrophic factors (e.g. GDNF, BDNF), and form Bands of Büngner that guide axon growth.',
    ],
    markers: [{ name: 'SOX10' }, { name: 'S100B' }, { name: 'c-Jun', note: 'repair program' }, { name: 'p75NTR' }],
    papers: [
      {
        title: 'The repair Schwann cell and its function in regenerating nerves',
        authors: 'Jessen KR, Mirsky R',
        journal: 'J Physiol',
        year: 2016,
        url: pubmed('Jessen Mirsky repair Schwann cell function regenerating nerves'),
      },
    ],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  graft_axon: {
    title: 'Axonal Profiles in Graft',
    category: 'graft',
    color: '#fde68a',
    summary: 'Donor axon remnants and/or host fibers within the graft.',
    description: [
      'Placeholder. Distinguish degenerating donor sural axons (Wallerian degeneration) from any host-derived fibers entering the graft.',
    ],
    markers: [{ name: 'NF-H' }, { name: 'β-III tubulin' }, { name: 'TH', note: 'if host DA fibers' }],
    papers: [{ title: 'Wallerian degeneration (search)', url: pubmed('Wallerian degeneration review') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  graft_macrophage: {
    title: 'Macrophage',
    category: 'graft',
    color: '#e1a0d1',
    summary: 'Myeloid cells clearing myelin debris and shaping the graft’s repair environment.',
    description: ['Placeholder. Discuss infiltration, debris clearance, and polarization states over time post-implant.'],
    markers: [{ name: 'CD68' }, { name: 'CD163' }, { name: 'IBA1' }],
    papers: [{ title: 'Macrophages in peripheral nerve repair (search)', url: pubmed('macrophages peripheral nerve regeneration review') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  endoneurial_fibroblast: {
    title: 'Endoneurial Fibroblast',
    category: 'graft',
    color: '#99e7d1',
    summary: 'Stromal cells producing extracellular matrix within the nerve.',
    description: ['Placeholder.'],
    markers: [{ name: 'PDGFRα' }, { name: 'CD34' }],
    papers: [{ title: 'Nerve fibroblasts (search)', url: pubmed('endoneurial fibroblasts peripheral nerve') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  col1a1_collagen: {
    title: 'COL1A1+ Collagen Fibrils',
    category: 'graft',
    color: '#a6eaaa',
    pickPriority: 'background',
    summary: 'Longitudinal type I collagen fibrils forming the graft’s extracellular scaffold.',
    description: [
      'Placeholder. Describe the endoneurial/epineurial collagen matrix of the graft and its persistence or remodelling after implantation.',
    ],
    markers: [{ name: 'COL1A1' }],
    papers: [{ title: 'Peripheral nerve extracellular matrix (search)', url: pubmed('peripheral nerve extracellular matrix collagen endoneurium') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  graft_vasculature: {
    title: 'Graft Vasculature',
    category: 'interface',
    color: '#dd657c',
    summary: 'Blood vessels revascularizing the graft from host tissue.',
    description: ['Placeholder. Describe revascularization and vessel density relative to host SN.'],
    markers: [{ name: 'CD31' }, { name: 'Collagen IV' }],
    papers: [{ title: 'Nerve graft revascularization (search)', url: pubmed('nerve graft revascularization') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  nigral_da_neuron: {
    title: 'Nigral Dopaminergic Neuron',
    category: 'host',
    color: '#50b5ff',
    summary: 'Neuromelanin-pigmented TH+ neurons projecting to the striatum; progressively lost in PD.',
    description: [
      'Placeholder. Describe neuron density and morphology near vs. distal to the graft.',
    ],
    markers: [{ name: 'TH' }, { name: 'DAT' }, { name: 'α-synuclein', note: 'pathology' }],
    papers: [{ title: 'Nigral dopaminergic neuron loss in PD (search)', url: pubmed('substantia nigra dopaminergic neuron loss Parkinson') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: 'nigrostriatal',
  },

  da_neurite_in_graft: {
    title: 'Dopaminergic Neurite at the Graft',
    category: 'interface',
    color: '#50c8ff',
    summary: 'Placeholder. Host dopaminergic processes extending toward and into the graft.',
    description: ['Placeholder. Describe evidence for host TH+ fibers at or within the graft.'],
    markers: [{ name: 'TH' }],
    papers: [],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },
  
  microglia: {
    title: 'Microglia',
    category: 'host',
    color: '#dae2f3',
    summary: 'Resident CNS immune cells responding at the graft–host interface.',
    description: ['Placeholder.'],
    markers: [{ name: 'IBA1' }, { name: 'TMEM119' }, { name: 'P2RY12' }],
    papers: [{ title: 'Microglia in Parkinson’s disease (search)', url: pubmed('microglia Parkinson substantia nigra') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  homeostatic_astrocyte: {
    title: 'Homeostatic Astrocyte',
    category: 'host',
    color: '#a0c8f1',
    summary: 'Astrocytes away from the graft, with fine, non-hypertrophic processes.',
    description: [
      'Placeholder. Contrast with reactive astrocytes at the graft boundary (smaller soma, thinner processes, little secondary branching).',
    ],
    markers: [{ name: 'ALDH1L1' }, { name: 'GFAP', note: 'low' }],
    papers: [{ title: 'Astrocyte heterogeneity and reactivity (search)', url: pubmed('astrocyte reactivity heterogeneity review') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  oligodendrocyte: {
    title: 'Oligodendrocyte',
    category: 'host',
    color: '#e7ddb5',
    summary: 'Myelinating glia of the host CNS.',
    description: ['Placeholder. Describe oligodendrocyte distribution in the SN and any changes near the graft.'],
    markers: [{ name: 'OLIG2' }, { name: 'MBP' }],
    papers: [{ title: 'Oligodendrocytes in Parkinson’s disease (search)', url: pubmed('oligodendrocytes Parkinson disease substantia nigra') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },

  astrocyte: {
    title: 'Reactive Astrocyte',
    category: 'interface',
    color: '#59eaff',
    summary: 'Astrocytes forming the glial boundary around the implanted graft.',
    description: ['Placeholder. Describe glial boundary formation and GFAP reactivity at the interface.'],
    markers: [{ name: 'GFAP' }, { name: 'ALDH1L1' }],
    papers: [{ title: 'Reactive astrocytes at CNS implants (search)', url: pubmed('reactive astrocytes glial scar transplant') }],
    assets: { circuitDiagramUrl: null, images: [], videos: [] },
    customPanel: null,
  },
};

/** Category labels + display order for the structure index. */
export const categories = {
  graft: 'Graft',
  interface: 'Graft–host interface',
  host: 'Host substantia nigra',
};

export const knownIds = Object.keys(cellData);
