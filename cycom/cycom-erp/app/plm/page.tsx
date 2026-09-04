'use client';

import React, { useState, useEffect } from 'react';
import { useCycomList, m2oName, fmtDate, type Many2One } from '@/lib/cycomModels';
import { create } from '@/lib/cycom';
import { Trash2 } from 'lucide-react';
import { useT } from '@/lib/i18n';

interface BomComponent {
  name: string;
  qtyNeeded: number;
  unitCost: number;
}

interface ProductBOM {
  id: string;
  productName: string;
  sku: string;
  components: BomComponent[];
}

interface EcoOrder {
  id: string;
  productName: string;
  title: string;
  reason: string;
  state: 'Draft' | 'Under Review' | 'Approved';
  dateCreated: string;
}

const INITIAL_BOMS: ProductBOM[] = [
  {
    id: 'BOM-001',
    productName: 'Premium Olive Oil 1L (Carton of 6)',
    sku: 'OLIVE-OIL-CARTON',
    components: [
      { name: 'Cold Pressed Olive Oil 1L', qtyNeeded: 6, unitCost: 4.50 },
      { name: 'Glass Bottles 1L', qtyNeeded: 6, unitCost: 0.35 },
      { name: 'Aluminum Caps', qtyNeeded: 6, unitCost: 0.05 },
      { name: 'Cardboard Box Outer', qtyNeeded: 1, unitCost: 0.80 },
    ]
  },
  {
    id: 'BOM-002',
    productName: 'Cycom Milk Powder 400g (Pack of 12)',
    sku: 'MILK-POW-PACK',
    components: [
      { name: 'Concentrated Milk Solids', qtyNeeded: 4.8, unitCost: 3.20 }, // kg
      { name: 'Tin Containers', qtyNeeded: 12, unitCost: 0.40 },
      { name: 'Plastic Lids', qtyNeeded: 12, unitCost: 0.10 },
      { name: 'Shrink Wrap Film', qtyNeeded: 1, unitCost: 0.50 },
    ]
  }
];

type CycomEco = {
  id: number;
  name?: string;
  product_tmpl_id?: Many2One;
  stage_id?: Many2One;
  user_id?: Many2One;
  create_date?: string;
};

const mapEcoState = (stageName: string): EcoOrder['state'] => {
  const n = stageName.toLowerCase();
  if (n.includes('review') || n.includes('progress')) return 'Under Review';
  if (n.includes('approv') || n.includes('done')) return 'Approved';
  return 'Draft';
};

const mapEco = (r: CycomEco): EcoOrder => ({
  id: r.name || `ECO-${r.id}`,
  productName: m2oName(r.product_tmpl_id, '—'),
  title: r.name || '—',
  reason: '',
  state: mapEcoState(m2oName(r.stage_id)),
  dateCreated: fmtDate(r.create_date),
});

const ECO_STATUS_KEY: Record<EcoOrder['state'], string> = {
  Draft: 'status.draft',
  'Under Review': 'status.waitingApproval',
  Approved: 'status.approved',
};

export default function PLMPage() {
  const t = useT();
  const { rows: liveEcos, loading } = useCycomList<CycomEco, EcoOrder>(
    'mrp.eco', [], ['name', 'product_tmpl_id', 'stage_id', 'user_id', 'create_date'],
    mapEco,
  );
  const [boms, setBoms] = useState<ProductBOM[]>(INITIAL_BOMS);
  const [ecos, setEcos] = useState<EcoOrder[]>([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!loading) setEcos(liveEcos); }, [loading]);

  // Selected BOM for details
  const [selectedBomId, setSelectedBomId] = useState('BOM-001');

  // Form states for adding BOM component
  const [compName, setCompName] = useState('');
  const [compQty, setCompQty] = useState('');
  const [compCost, setCompCost] = useState('');

  // Form states for creating ECO
  const [ecoProd, setEcoProd] = useState('Premium Olive Oil 1L (Carton of 6)');
  const [ecoTitle, setEcoTitle] = useState('');
  const [ecoReason, setEcoReason] = useState('');

  const selectedBOM = boms.find(b => b.id === selectedBomId) || boms[0];

  // Calculate Rollup Cost
  const rollupCost = selectedBOM.components.reduce((acc, curr) => acc + (curr.qtyNeeded * curr.unitCost), 0);

  const handleAddComponent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!compName || !compQty || !compCost) return;

    const newComp: BomComponent = {
      name: compName,
      qtyNeeded: parseFloat(compQty),
      unitCost: parseFloat(compCost)
    };

    setBoms(boms.map(bom => {
      if (bom.id === selectedBomId) {
        return {
          ...bom,
          components: [...bom.components, newComp]
        };
      }
      return bom;
    }));

    setCompName('');
    setCompQty('');
    setCompCost('');
  };

  const handleDeleteComponent = (name: string) => {
    setBoms(boms.map(bom => {
      if (bom.id === selectedBomId) {
        return {
          ...bom,
          components: bom.components.filter(c => c.name !== name)
        };
      }
      return bom;
    }));
  };

  const handleCreateECO = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ecoTitle || !ecoReason) return;

    try {
      const id = await create('mrp.eco', {
        name: ecoTitle,
        title: ecoTitle,
        product_name: ecoProd,
        reason: ecoReason,
      });
      const newEco: EcoOrder = {
        id: `ECO-${id}`,
        productName: ecoProd,
        title: ecoTitle,
        reason: ecoReason,
        state: 'Draft',
        dateCreated: new Date().toISOString().split('T')[0]
      };
      setEcos([newEco, ...ecos]);
      setEcoTitle('');
      setEcoReason('');
    } catch {
      /* keep form for retry */
    }
  };

  const advanceECO = (id: string) => {
    setEcos(ecos.map(eco => {
      if (eco.id === id) {
        const nextState = eco.state === 'Draft' ? 'Under Review' : 'Approved';
        return { ...eco, state: nextState as any };
      }
      return eco;
    }));
  };

  if (loading) return <div style={{padding:'2rem',color:'#ccc'}}>{t('plmDash.loading')}</div>;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">{t('plmDash.title')}</h1>
          <p className="page-subtitle">{t('plmDash.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column - BOM Selector & Component Creator */}
        <div className="space-y-6">

          {/* BOM Selector */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">{t('plmDash.bomSelectorHeading')}</h2>
            <div className="space-y-2">
              {boms.map(bom => (
                <div
                  key={bom.id}
                  onClick={() => setSelectedBomId(bom.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    selectedBomId === bom.id
                      ? 'bg-gradient-to-br from-orange-500/12 to-blue-500/8 border-orange-500/25 text-white'
                      : 'border-transparent hover:bg-white/3 text-slate-400'
                  }`}
                >
                  <p className="text-xs font-bold">{bom.productName}</p>
                  <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                    <span>{t('plmDash.sku', { sku: bom.sku })}</span>
                    <span>{t('plmDash.componentsN', { n: bom.components.length })}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add Component to BOM */}
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-2">{t('plmDash.addComponentHeading')}</h3>
            <form onSubmit={handleAddComponent} className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">{t('plmDash.componentName')}</label>
                <input
                  type="text"
                  required
                  placeholder={t('plmDash.componentNamePh')}
                  value={compName}
                  onChange={e => setCompName(e.target.value)}
                  className="input-field py-1"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('plmDash.qtyNeeded')}</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder={t('plmDash.qtyNeededPh')}
                    value={compQty}
                    onChange={e => setCompQty(e.target.value)}
                    className="input-field py-1 font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('plmDash.unitCost')}</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder={t('plmDash.unitCostPh')}
                    value={compCost}
                    onChange={e => setCompCost(e.target.value)}
                    className="input-field py-1 font-mono"
                  />
                </div>
              </div>
              <button type="submit" className="btn-primary w-full py-1.5 mt-2">
                {t('plmDash.addRawMaterial')}
              </button>
            </form>
          </div>

        </div>

        {/* Right Column - BOM cost rollups & ECO pipelines */}
        <div className="lg:col-span-2 space-y-6">

          {/* Cost Rollup Sheet */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('plmDash.rollupHeading')}</h2>
              <span className="text-[10px] bg-purple-500/20 text-[#A855F7] border border-[#A855F7]/30 px-2 py-0.5 rounded font-bold font-mono">
                {selectedBOM.sku}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('plmDash.colComponentName')}</th>
                    <th>{t('plmDash.colQtyNeeded')}</th>
                    <th>{t('plmDash.colUnitCost')}</th>
                    <th>{t('plmDash.colTotalCost')}</th>
                    <th className="text-end">{t('plmDash.colAction')}</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedBOM.components.map((c, i) => {
                    const totalCost = c.qtyNeeded * c.unitCost;
                    return (
                      <tr key={i}>
                        <td className="font-bold text-slate-300">{c.name}</td>
                        <td className="font-mono">{c.qtyNeeded}</td>
                        <td className="font-mono">JOD {c.unitCost.toFixed(2)}</td>
                        <td className="font-mono font-bold text-white">JOD {totalCost.toFixed(2)}</td>
                        <td className="text-end">
                          <button
                            onClick={() => handleDeleteComponent(c.name)}
                            className="p-1 rounded hover:bg-red-500/20 text-[#EF4444]"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {/* Total Rollup row */}
                  <tr className="border-t border-white/10 bg-white/2">
                    <td colSpan={3} className="font-black text-end text-slate-400 uppercase tracking-wide">{t('plmDash.rollupCostLabel')}</td>
                    <td colSpan={2} className="font-black text-emerald-400 text-sm">JOD {rollupCost.toFixed(2)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* ECO Pipeline approvals */}
          <div className="glass-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">{t('plmDash.ecoHeading')}</h2>
              <span className="badge badge-cyan text-[8px]">{t('plmDash.ecoWorkflow')}</span>
            </div>

            <div className="space-y-3">
              {ecos.map(eco => (
                <div key={eco.id} className="p-4 rounded-xl bg-white/3 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black text-white">{eco.id}</span>
                      <span className="text-[10px] text-slate-500">{eco.dateCreated}</span>
                      <span className={`badge text-[9px] ${
                        eco.state === 'Approved' ? 'badge-green' :
                        eco.state === 'Under Review' ? 'badge-yellow' : 'badge-cyan'
                      }`}>{t(ECO_STATUS_KEY[eco.state])}</span>
                    </div>
                    <p className="text-xs text-slate-200 font-bold">{eco.title}</p>
                    <p className="text-[11px] text-slate-400 font-medium">{t('plmDash.bomCause', { product: eco.productName, reason: eco.reason })}</p>
                  </div>

                  {eco.state !== 'Approved' && (
                    <button
                      onClick={() => advanceECO(eco.id)}
                      className="p-1.5 px-3 text-[10px] font-bold rounded bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/25 text-[#00F0FF] flex-shrink-0"
                    >
                      {eco.state === 'Draft' ? t('plmDash.submitForReview') : t('plmDash.confirmApproval')}
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* Create ECO Form */}
            <form onSubmit={handleCreateECO} className="grid grid-cols-1 md:grid-cols-2 gap-3 border-t border-white/5 pt-4 text-xs items-end">
              <div className="space-y-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('plmDash.targetBom')}</label>
                  <select value={ecoProd} onChange={e => setEcoProd(e.target.value)} className="input-field py-1">
                    {boms.map(bom => <option key={bom.id} value={bom.productName}>{bom.productName}</option>)}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('plmDash.ecoTitle')}</label>
                  <input
                    type="text"
                    required
                    placeholder={t('plmDash.ecoTitlePh')}
                    value={ecoTitle}
                    onChange={e => setEcoTitle(e.target.value)}
                    className="input-field py-1"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase">{t('plmDash.ecoReason')}</label>
                  <input
                    type="text"
                    required
                    placeholder={t('plmDash.ecoReasonPh')}
                    value={ecoReason}
                    onChange={e => setEcoReason(e.target.value)}
                    className="input-field py-1"
                  />
                </div>
                <button type="submit" className="btn-primary w-full py-1.5">
                  {t('plmDash.launchEco')}
                </button>
              </div>
            </form>
          </div>

        </div>

      </div>
    </div>
  );
}
