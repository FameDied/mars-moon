import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import {
  DEFAULT_CUTOFFS, DEFAULT_WEIGHTS, evaluateAll, findSplitTwin, loadAtlasDataset,
  type AtlasDataset, type BodyId, type CelestialId, type Cutoffs, type PlanetarySite, type SiteEval, type SplitTwinMatch, type Weights,
} from '../data/atlasData';

export type CardId = 'brief' | 'radar' | 'shield' | 'power';
export interface Callout { key: number; title: string; body: string; tone: 'ok' | 'info' | 'warn' }
export interface FlyTo { siteId: string; zoomRadii: number | null; nonce: number }

interface Ctx {
  dataset: AtlasDataset | null;
  stage: 'hero' | 'workspace';
  heroVisible: boolean;
  focus: CelestialId;
  body: BodyId;
  weights: Weights;
  cutoffs: Cutoffs;
  selectedId: string | null;
  selected: PlanetarySite | null;
  flyTo: FlyTo | null;
  evalMap: Map<string, SiteEval>;
  qualified: number;
  total: number;
  topIds: Record<BodyId, string | null>;
  tube: boolean;
  openOnly: boolean;
  docked: CardId[];
  tour: number | null;
  repoOpen: boolean;
  leftOpen: boolean;
  rightOpen: boolean;
  callout: Callout | null;
  activePreset: string | null;
  selectedAnalogId: string | null;
  twin: SplitTwinMatch | null;
  sceneReady: boolean;
  launch: () => void;
  focusBody: (b: BodyId) => void;
  focusEarth: () => void;
  selectSite: (id: string) => void;
  applyPreset: (id: string) => void;
  setWeight: (k: keyof Weights, v: number) => void;
  setCutoff: (k: keyof Cutoffs, v: number) => void;
  setTube: (v: boolean) => void;
  setOpenOnly: (v: boolean) => void;
  dock: (c: CardId) => void;
  undock: (c: CardId) => void;
  setTour: (n: number | null) => void;
  setRepoOpen: (v: boolean) => void;
  setLeftOpen: (v: boolean) => void;
  setRightOpen: (v: boolean) => void;
  dismissCallout: () => void;
  setSelectedAnalogId: (id: string | null) => void;
  onSettled: (key: string) => void;
  onSceneReady: () => void;
}

const AtlasCtx = createContext<Ctx | null>(null);
export const useAtlas = () => {
  const c = useContext(AtlasCtx);
  if (!c) throw new Error('AtlasProvider missing');
  return c;
};

export function AtlasProvider({ children }: { children: ReactNode }) {
  const [dataset, setDataset] = useState<AtlasDataset | null>(null);
  const [stage, setStage] = useState<'hero' | 'workspace'>('hero');
  const [heroVisible, setHeroVisible] = useState(true);
  const [focus, setFocus] = useState<CelestialId>('moon');
  const [body, setBody] = useState<BodyId>('moon');
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);
  const [cutoffs, setCutoffs] = useState<Cutoffs>(DEFAULT_CUTOFFS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [flyTo, setFlyTo] = useState<FlyTo | null>(null);
  const [tube, setTube] = useState(false);
  const [openOnly, setOpenOnly] = useState(false);
  const [docked, setDocked] = useState<CardId[]>([]);
  const [tour, setTour] = useState<number | null>(null);
  const [repoOpen, setRepoOpen] = useState(false);
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [callout, setCallout] = useState<Callout | null>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [selectedAnalogId, setSelectedAnalogId] = useState<string | null>(null);
  const [sceneReady, setSceneReady] = useState(false);
  const nonce = useRef(0);
  const tourPending = useRef(true);

  useEffect(() => {
    loadAtlasDataset().then((d) => { setDataset(d); setSelectedId(d.meta.defaultSiteId.moon); });
  }, []);

  const evalMap = useMemo(() => (dataset ? evaluateAll(dataset.sites, weights, cutoffs) : new Map<string, SiteEval>()), [dataset, weights, cutoffs]);
  const qualified = useMemo(() => { let n = 0; evalMap.forEach((v) => { if (v.go) n++; }); return n; }, [evalMap]);
  const topIds = useMemo(() => {
    const t: Record<BodyId, { id: string; u: number } | null> = { moon: null, mars: null };
    dataset?.sites.forEach((s) => {
      const e = evalMap.get(s.id);
      if (e?.go && (!t[s.body] || e.u > t[s.body]!.u)) t[s.body] = { id: s.id, u: e.u };
    });
    return { moon: t.moon?.id ?? null, mars: t.mars?.id ?? null };
  }, [dataset, evalMap]);
  const selected = useMemo(() => dataset?.sites.find((s) => s.id === selectedId) ?? null, [dataset, selectedId]);
  const twin = useMemo(() => (dataset ? findSplitTwin(dataset.analogs, body, openOnly) : null), [dataset, body, openOnly]);

  const fly = useCallback((siteId: string, zoomRadii: number | null) => setFlyTo({ siteId, zoomRadii, nonce: ++nonce.current }), []);

  const launch = useCallback(() => {
    setStage('workspace');
    setHeroVisible(false);
    setFocus('moon');
  }, []);

  const showCallout = useCallback((c: Omit<Callout, 'key'>) => setCallout({ ...c, key: Date.now() }), []);
  useEffect(() => {
    if (!callout) return;
    const t = setTimeout(() => setCallout(null), 11000);
    return () => clearTimeout(t);
  }, [callout]);

  const focusBody = useCallback((b: BodyId) => {
    if (!dataset) return;
    setBody(b);
    setFocus(b);
    setSelectedAnalogId(null);
    const cur = dataset.sites.find((s) => s.id === selectedId);
    if (!cur || cur.body !== b) {
      const id = dataset.meta.defaultSiteId[b];
      setSelectedId(id);
      fly(id, null);
    }
  }, [dataset, selectedId, fly]);

  const focusEarth = useCallback(() => setFocus('earth'), []);

  const selectSite = useCallback((id: string) => {
    const s = dataset?.sites.find((x) => x.id === id);
    if (!s) return;
    setSelectedId(id);
    if (s.body !== body) setBody(s.body);
    fly(id, null);
  }, [dataset, body, fly]);

  const applyPreset = useCallback((id: string) => {
    const p = dataset?.presets.find((x) => x.id === id);
    if (!p) return;
    setActivePreset(id);
    setWeights(p.weights);
    setBody(p.body);
    setFocus(p.body);
    setSelectedId(p.siteId);
    fly(p.siteId, p.zoomRadii);
    showCallout(p.callout);
  }, [dataset, fly, showCallout]);

  const setWeight = useCallback((k: keyof Weights, v: number) => { setActivePreset(null); setWeights((w) => ({ ...w, [k]: v })); }, []);
  const setCutoff = useCallback((k: keyof Cutoffs, v: number) => setCutoffs((c) => ({ ...c, [k]: v })), []);
  const dock = useCallback((c: CardId) => setDocked((d) => (d.includes(c) ? d : [...d, c])), []);
  const undock = useCallback((c: CardId) => setDocked((d) => d.filter((x) => x !== c)), []);
  const onSettled = useCallback((key: string) => {
    if (key === 'moon' && tourPending.current) { tourPending.current = false; setTimeout(() => setTour(0), 500); }
  }, []);
  const onSceneReady = useCallback(() => setSceneReady(true), []);

  const value: Ctx = {
    dataset, stage, heroVisible, focus, body, weights, cutoffs, selectedId, selected, flyTo, evalMap, qualified,
    total: dataset?.sites.length ?? 0, topIds, tube, openOnly, docked, tour, repoOpen, leftOpen, rightOpen, callout, activePreset,
    selectedAnalogId, twin, sceneReady,
    launch, focusBody, focusEarth, selectSite, applyPreset, setWeight, setCutoff, setTube, setOpenOnly, dock, undock, setTour,
    setRepoOpen, setLeftOpen, setRightOpen, dismissCallout: () => setCallout(null), setSelectedAnalogId, onSettled, onSceneReady,
  };
  return <AtlasCtx.Provider value={value}>{children}</AtlasCtx.Provider>;
}
