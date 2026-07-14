'use client';

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShoppingCart, Lock, Unlock, ArrowDownRight, ArrowUpRight, 
  Calendar, CreditCard, ChevronRight, CheckCircle, Calculator,
  Search, X, Plus, Minus, Trash2, Printer, Banknote, Smartphone,
  ReceiptText, ScanBarcode, Tag, Package, ArrowLeft
} from 'lucide-react';
import { useCompany } from '@/context/CompanyContext';
import { useCycomList, fmtDate, m2oName, type Many2One } from '@/lib/cycomModels';

// ── Product Catalog ──
interface Product {
  id: string;
  barcode: string;
  name: string;
  nameAr: string;
  category: string;
  price: number;
  taxRate: number;
  stock: number;
  image: string;
}

const PRODUCTS: Product[] = [
  // Supermarket / Groceries
  { id: 'PRD-001', barcode: '6281000000101', name: 'Premium Olive Oil 1L', nameAr: 'زيت زيتون ممتاز', category: 'Groceries', price: 7.50, taxRate: 0.16, stock: 340, image: '🫒' },
  { id: 'PRD-002', barcode: '6281000000102', name: 'Cycom Tahini 400g', nameAr: 'طحينة الأنبتاوي', category: 'Groceries', price: 3.25, taxRate: 0.16, stock: 520, image: '🥜' },
  { id: 'PRD-003', barcode: '6281000000103', name: 'Organic Honey 500g', nameAr: 'عسل عضوي', category: 'Groceries', price: 12.00, taxRate: 0.16, stock: 180, image: '🍯' },
  { id: 'PRD-004', barcode: '6281000000104', name: 'Mixed Nuts 250g', nameAr: 'مكسرات مشكلة', category: 'Groceries', price: 5.50, taxRate: 0.16, stock: 410, image: '🥜' },
  { id: 'PRD-005', barcode: '6281000000105', name: 'Fresh Milk 1L', nameAr: 'حليب طازج', category: 'Groceries', price: 1.20, taxRate: 0, stock: 890, image: '🥛' },
  { id: 'PRD-006', barcode: '6281000000106', name: 'Za\'atar Blend 200g', nameAr: 'خلطة زعتر', category: 'Groceries', price: 2.80, taxRate: 0.16, stock: 650, image: '🌿' },
  { id: 'PRD-007', barcode: '6281000000107', name: 'Labneh 500g', nameAr: 'لبنة', category: 'Groceries', price: 2.50, taxRate: 0, stock: 720, image: '🫙' },
  { id: 'PRD-008', barcode: '6281000000108', name: 'Arabic Coffee 250g', nameAr: 'قهوة عربية', category: 'Beverages', price: 8.00, taxRate: 0.16, stock: 300, image: '☕' },
  { id: 'PRD-009', barcode: '6281000000109', name: 'Olive Oil Soap (3pc)', nameAr: 'صابون زيت زيتون', category: 'Personal Care', price: 4.50, taxRate: 0.16, stock: 220, image: '🧼' },
  { id: 'PRD-010', barcode: '6281000000110', name: 'Halloumi Cheese 250g', nameAr: 'جبنة حلوم', category: 'Groceries', price: 3.80, taxRate: 0, stock: 400, image: '🧀' },
  { id: 'PRD-011', barcode: '6281000000111', name: 'Maamoul Date Cookies 12pc', nameAr: 'معمول تمر', category: 'Bakery', price: 6.00, taxRate: 0.16, stock: 280, image: '🍪' },
  { id: 'PRD-012', barcode: '6281000000112', name: 'Sparkling Water 6×500ml', nameAr: 'مياه فوارة', category: 'Beverages', price: 3.00, taxRate: 0, stock: 960, image: '💧' },
  
  // Cafe Items
  { id: 'PRD-CAF-01', barcode: '6282000000101', name: 'Espresso Single', nameAr: 'إسبريسو سينجل', category: 'Coffee', price: 1.80, taxRate: 0.16, stock: 999, image: '☕' },
  { id: 'PRD-CAF-02', barcode: '6282000000102', name: 'Cappuccino Double', nameAr: 'كابتشينو دبل', category: 'Coffee', price: 2.50, taxRate: 0.16, stock: 999, image: '☕' },
  { id: 'PRD-CAF-03', barcode: '6282000000103', name: 'Chocolate Chip Muffin', nameAr: 'مافن الشوكولاتة', category: 'Bakery & Sweets', price: 2.20, taxRate: 0.16, stock: 50, image: '🧁' },
  { id: 'PRD-CAF-04', barcode: '6282000000104', name: 'Butter Croissant', nameAr: 'كرواسون زبدة', category: 'Bakery & Sweets', price: 1.90, taxRate: 0.16, stock: 80, image: '🥐' },
  { id: 'PRD-CAF-05', barcode: '6282000000105', name: 'Iced Matcha Latte', nameAr: 'ماتشا مثلج', category: 'Cold Drinks', price: 3.50, taxRate: 0.16, stock: 200, image: '🍵' },
  
  // Restaurant Items
  { id: 'PRD-RES-01', barcode: '6283000000101', name: 'Traditional Mansaf Feast', nameAr: 'وجبة منسف بلدي', category: 'Platters', price: 12.50, taxRate: 0.16, stock: 120, image: '🥘' },
  { id: 'PRD-RES-02', barcode: '6283000000102', name: 'Mixed Grill Skewers', nameAr: 'مشاوي مشكلة', category: 'Platters', price: 9.80, taxRate: 0.16, stock: 150, image: '🍢' },
  { id: 'PRD-RES-03', barcode: '6283000000103', name: 'Hummus & Falafel Plate', nameAr: 'صحن حمص وفلافل', category: 'Appetizers', price: 3.50, taxRate: 0.16, stock: 300, image: '🧆' },
  { id: 'PRD-RES-04', barcode: '6283000000104', name: 'Tabbouleh Salad Fresh', nameAr: 'تبولة طازجة', category: 'Salads & Sides', price: 2.20, taxRate: 0.16, stock: 250, image: '🥗' },
  
  // Car Showroom / Merchandise
  { id: 'PRD-CAR-01', barcode: '6284000000101', name: 'CyberCom Model S Coupe', nameAr: 'سايبركوم كوبيه إس', category: 'Vehicles', price: 42000.00, taxRate: 0.16, stock: 5, image: '🏎️' },
  { id: 'PRD-CAR-02', barcode: '6284000000102', name: 'CyberCom SUV Touring EV', nameAr: 'سايبركوم دفع رباعي كهربائي', category: 'Vehicles', price: 58000.00, taxRate: 0.16, stock: 3, image: '🚙' },
  { id: 'PRD-CAR-03', barcode: '6284000000103', name: 'CyberCom Hypercar Concept', nameAr: 'سيارة خارقة نموذجية', category: 'Vehicles', price: 120000.00, taxRate: 0.16, stock: 1, image: '🏎️' },
  { id: 'PRD-CAR-04', barcode: '6284000000104', name: 'Scale Model CyberCom (1:18)', nameAr: 'مجسم سيارة صغير', category: 'Merchandise', price: 45.00, taxRate: 0.16, stock: 40, image: '🚗' },
  { id: 'PRD-CAR-05', barcode: '6284000000105', name: 'CyberCom Racing Cap', nameAr: 'كاب سباق سايبركوم', category: 'Merchandise', price: 15.00, taxRate: 0.16, stock: 100, image: '🧢' }
];

// Fallback empty categories array which will be overriden dynamically
const CATEGORIES: string[] = [];

// ── Order Line ──
interface OrderLine {
  product: Product;
  qty: number;
  discount: number;
}

// ── Cash Move ──
interface CashMove {
  id: string;
  type: 'Cash-In' | 'Cash-Out';
  amount: number;
  reason: string;
  timestamp: string;
}

// ── POS Order ──
interface PosOrder {
  id: string;
  customerName: string;
  type: 'Advance Order' | 'Pledge Order';
  total: number;
  deposit: number;
  deadlineDate: string;
  status: 'Pending' | 'Fulfilled' | 'Overdue';
}

type PosView = 'terminal' | 'orders' | 'receipt';

type CyPosSession = {
  id: number;
  name?: string;
  user_id?: Many2One;
  config_id?: Many2One;
  start_at?: string;
  stop_at?: string;
  state?: string;
  cash_register_balance_end_real?: number;
};

const mapSession = (r: CyPosSession): PosOrder => ({
  id: r.name || `SES-${r.id}`,
  customerName: m2oName(r.user_id, '—'),
  type: 'Advance Order',
  total: r.cash_register_balance_end_real ?? 0,
  deposit: 0,
  deadlineDate: r.stop_at ? fmtDate(r.stop_at) : r.start_at ? fmtDate(r.start_at) : '—',
  status: r.state === 'closed' ? 'Fulfilled' : r.state === 'opened' ? 'Pending' : 'Overdue',
});

export default function PosDashboard() {
  const { activeCompany, activeBranch } = useCompany();
  
  // Session state
  const [sessionOpen, setSessionOpen] = useState(true);
  const [posView, setPosView] = useState<PosView>('terminal');
  
  // Product browsing
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [barcodeInput, setBarcodeInput] = useState('');

  // Order state
  const [orderLines, setOrderLines] = useState<OrderLine[]>([]);
  const [customerName, setCustomerName] = useState('Walk-in Customer');
  
  // Payment state
  const [showPayment, setShowPayment] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'card' | 'split'>('cash');
  const [cashTendered, setCashTendered] = useState('');
  const [lastReceipt, setLastReceipt] = useState<{id: string; lines: OrderLine[]; total: number; tax: number; payment: string; change: number; date: string; customer: string} | null>(null);

  // Cash moves
  const [cashMoves, setCashMoves] = useState<CashMove[]>([
    { id: 'CM-01', type: 'Cash-In', amount: 200, reason: 'Opening float addition', timestamp: '08:00:00' },
  ]);
  const [moveType, setMoveType] = useState<'Cash-In' | 'Cash-Out'>('Cash-In');
  const [moveAmt, setMoveAmt] = useState('');
  const [moveReason, setMoveReason] = useState('');

  // Advance/Pledge orders — wired to live pos.session data
  const { rows: sessionOrders, loading: sessionsLoading } = useCycomList<CyPosSession, PosOrder>(
    'pos.session',
    [],
    ['name', 'user_id', 'config_id', 'start_at', 'stop_at', 'state', 'cash_register_balance_end_real'],
    mapSession,
    { order: 'start_at desc' },
  );
  const [newLocalOrders, setNewLocalOrders] = useState<PosOrder[]>([]);
  const [fulfilledIds, setFulfilledIds] = useState<string[]>([]);
  const orders = [
    ...newLocalOrders,
    ...sessionOrders.map(o => fulfilledIds.includes(o.id) ? { ...o, status: 'Fulfilled' as const } : o),
  ];
  const [orderCust, setOrderCust] = useState('');
  const [orderType, setOrderType] = useState<'Advance Order' | 'Pledge Order'>('Advance Order');
  const [orderTotal, setOrderTotal] = useState('');
  const [orderDeposit, setOrderDeposit] = useState('');
  const [orderDeadline, setOrderDeadline] = useState('');

  // Rounding
  const roundingStrategy = 0.05;

  const storeName = activeBranch || (activeCompany.type === 'retail' && activeCompany.branches ? activeCompany.branches[0] : activeCompany.shortName);

  // ── Derived data (Dynamic Terminal Filtering) ──
  const filteredProducts = useMemo(() => {
    let branchProducts = PRODUCTS;
    const branchNameLower = (storeName || '').toLowerCase();
    
    if (branchNameLower.includes('café') || branchNameLower.includes('cafe')) {
      branchProducts = PRODUCTS.filter(p => ['Coffee', 'Bakery & Sweets', 'Cold Drinks'].includes(p.category));
    } else if (branchNameLower.includes('restaurant')) {
      branchProducts = PRODUCTS.filter(p => ['Platters', 'Appetizers', 'Salads & Sides'].includes(p.category));
    } else if (branchNameLower.includes('car') || branchNameLower.includes('showroom')) {
      branchProducts = PRODUCTS.filter(p => ['Vehicles', 'Merchandise'].includes(p.category));
    } else {
      // Default / Supermarket
      branchProducts = PRODUCTS.filter(p => ['Groceries', 'Beverages'].includes(p.category));
    }

    return branchProducts.filter(p => {
      const matchesCategory = activeCategory === 'All' || p.category === activeCategory;
      const matchesSearch = searchQuery === '' || 
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.barcode.includes(searchQuery) ||
        p.nameAr.includes(searchQuery);
      return matchesCategory && matchesSearch;
    });
  }, [activeCategory, searchQuery, storeName]);

  const CATEGORIES = useMemo(() => {
    let branchProducts = PRODUCTS;
    const branchNameLower = (storeName || '').toLowerCase();
    
    if (branchNameLower.includes('café') || branchNameLower.includes('cafe')) {
      branchProducts = PRODUCTS.filter(p => ['Coffee', 'Bakery & Sweets', 'Cold Drinks'].includes(p.category));
    } else if (branchNameLower.includes('restaurant')) {
      branchProducts = PRODUCTS.filter(p => ['Platters', 'Appetizers', 'Salads & Sides'].includes(p.category));
    } else if (branchNameLower.includes('car') || branchNameLower.includes('showroom')) {
      branchProducts = PRODUCTS.filter(p => ['Vehicles', 'Merchandise'].includes(p.category));
    } else {
      branchProducts = PRODUCTS.filter(p => ['Groceries', 'Beverages'].includes(p.category));
    }
    
    return ['All', ...new Set(branchProducts.map(p => p.category))];
  }, [storeName]);

  const subtotal = orderLines.reduce((acc, line) => acc + (line.product.price * line.qty * (1 - line.discount / 100)), 0);
  const taxTotal = orderLines.reduce((acc, line) => acc + (line.product.price * line.qty * (1 - line.discount / 100) * line.product.taxRate), 0);
  const rawTotal = subtotal + taxTotal;
  const roundedTotal = Math.round(rawTotal / roundingStrategy) * roundingStrategy;
  const roundingAdj = roundedTotal - rawTotal;
  const cashFloat = 200 + cashMoves.reduce((acc, curr) => acc + (curr.type === 'Cash-In' ? curr.amount : -curr.amount), 0);

  // ── Handlers ──
  const addToOrder = (product: Product) => {
    const existing = orderLines.find(l => l.product.id === product.id);
    if (existing) {
      setOrderLines(orderLines.map(l => l.product.id === product.id ? { ...l, qty: l.qty + 1 } : l));
    } else {
      setOrderLines([...orderLines, { product, qty: 1, discount: 0 }]);
    }
  };

  const handleBarcodeScan = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && barcodeInput) {
      const found = PRODUCTS.find(p => p.barcode === barcodeInput);
      if (found) addToOrder(found);
      setBarcodeInput('');
    }
  };

  const updateQty = (productId: string, delta: number) => {
    setOrderLines(orderLines.map(l => {
      if (l.product.id === productId) {
        const newQty = l.qty + delta;
        return newQty <= 0 ? l : { ...l, qty: newQty };
      }
      return l;
    }).filter(l => l.qty > 0));
  };

  const removeFromOrder = (productId: string) => {
    setOrderLines(orderLines.filter(l => l.product.id !== productId));
  };

  const setDiscount = (productId: string, discount: number) => {
    setOrderLines(orderLines.map(l => l.product.id === productId ? { ...l, discount } : l));
  };

  const processPayment = () => {
    const cashGiven = parseFloat(cashTendered) || 0;
    const change = paymentMethod === 'cash' ? cashGiven - roundedTotal : 0;
    
    const receiptId = `RCP-${Date.now().toString(36).toUpperCase()}`;
    setLastReceipt({
      id: receiptId,
      lines: [...orderLines],
      total: roundedTotal,
      tax: taxTotal,
      payment: paymentMethod === 'cash' ? `Cash JOD ${cashGiven.toFixed(2)}` : paymentMethod === 'card' ? 'Card Terminal' : 'Split Payment',
      change: Math.max(0, change),
      date: new Date().toLocaleString(),
      customer: customerName,
    });

    if (paymentMethod === 'cash') {
      setCashMoves([...cashMoves, { id: `CM-${Date.now()}`, type: 'Cash-In', amount: roundedTotal, reason: `Sale ${receiptId}`, timestamp: new Date().toLocaleTimeString() }]);
    }

    setOrderLines([]);
    setCustomerName('Walk-in Customer');
    setCashTendered('');
    setShowPayment(false);
    setPosView('receipt');
  };

  const handleCashMoveSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!moveAmt || !moveReason) return;
    setCashMoves([...cashMoves, { id: `CM-${Date.now()}`, type: moveType, amount: parseFloat(moveAmt), reason: moveReason, timestamp: new Date().toLocaleTimeString() }]);
    setMoveAmt('');
    setMoveReason('');
  };

  const handleCreateOrder = (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderCust || !orderTotal || !orderDeadline) return;
    setNewLocalOrders(prev => [{ id: `POS-${orderType === 'Advance Order' ? 'ADV' : 'PLG'}-${Math.floor(200 + Math.random() * 800)}`, customerName: orderCust, type: orderType, total: parseFloat(orderTotal), deposit: orderType === 'Advance Order' ? parseFloat(orderDeposit) || 0 : 0, deadlineDate: orderDeadline, status: 'Pending' }, ...prev]);
    setOrderCust(''); setOrderTotal(''); setOrderDeposit(''); setOrderDeadline('');
  };

  // ── POS Terminal View ──
  if (posView === 'terminal' && sessionOpen) {
    return (
      <div className="space-y-0 -m-6 flex flex-col h-[calc(100vh-var(--topbar-height))]">
        {/* POS Header Bar */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-white/5 bg-[#0a0f1e]/50 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-bold text-white">POS SESSION ACTIVE</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">• {storeName}</span>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setPosView('orders')} className="text-[11px] text-slate-400 hover:text-white transition-colors font-medium">
              Orders & Pledges
            </button>
            <button onClick={() => setSessionOpen(false)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-[11px] font-bold hover:bg-red-500/20 transition-colors">
              <Lock className="w-3.5 h-3.5" /> Close Session
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* LEFT: Product Catalog */}
          <div className="flex-1 flex flex-col border-r border-white/5 overflow-hidden">
            {/* Search & Barcode */}
            <div className="px-4 py-3 flex gap-3 border-b border-white/5 flex-shrink-0">
              <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-3 py-1.5 flex-1">
                <Search className="w-4 h-4 text-slate-500" />
                <input 
                  type="text" placeholder="Search products..." 
                  value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full"
                />
              </div>
              <div className="flex items-center gap-2 bg-white/3 border border-white/8 rounded-xl px-3 py-1.5 w-[200px]">
                <ScanBarcode className="w-4 h-4 text-[#E67E22]" />
                <input 
                  type="text" placeholder="Scan barcode..." 
                  value={barcodeInput} onChange={e => setBarcodeInput(e.target.value)}
                  onKeyDown={handleBarcodeScan}
                  className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full font-mono"
                />
              </div>
            </div>

            {/* Category Pills */}
            <div className="px-4 py-2 flex gap-2 overflow-x-auto flex-shrink-0">
              {CATEGORIES.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1 rounded-full text-[10px] font-bold whitespace-nowrap transition-all ${
                    activeCategory === cat 
                      ? 'bg-[#E67E22]/20 text-[#E67E22] border border-[#E67E22]/30' 
                      : 'bg-white/5 text-slate-400 border border-transparent hover:bg-white/10'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Product Grid */}
            <div className="flex-1 overflow-y-auto p-4 grid grid-cols-3 xl:grid-cols-4 gap-3 content-start">
              {filteredProducts.map(product => (
                <button
                  key={product.id}
                  onClick={() => addToOrder(product)}
                  className="p-3 rounded-xl bg-white/3 border border-white/5 hover:border-[#E67E22]/30 hover:bg-[#E67E22]/5 transition-all text-left group"
                >
                  <div className="text-2xl mb-2">{product.image}</div>
                  <p className="text-[11px] font-bold text-white group-hover:text-[#E67E22] transition-colors leading-tight">{product.name}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">{product.nameAr}</p>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-xs font-black text-[#10B981]">JOD {product.price.toFixed(2)}</span>
                    <span className="text-[9px] text-slate-500 font-mono">{product.stock} in stock</span>
                  </div>
                  {product.taxRate > 0 && (
                    <span className="text-[8px] text-amber-400/70 font-bold mt-1 block">+{(product.taxRate * 100).toFixed(0)}% VAT</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* RIGHT: Order Panel */}
          <div className="w-[380px] flex flex-col bg-[#0b0f19]">
            {/* Customer */}
            <div className="px-4 py-3 border-b border-white/5 flex-shrink-0">
              <input 
                type="text" value={customerName} onChange={e => setCustomerName(e.target.value)}
                className="bg-white/3 border border-white/8 rounded-lg px-3 py-1.5 text-xs text-white w-full outline-none focus:border-[#E67E22]/50"
                placeholder="Customer name..."
              />
            </div>

            {/* Order Lines */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
              {orderLines.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-500">
                  <ShoppingCart className="w-10 h-10 mb-3 opacity-30" />
                  <p className="text-xs font-medium">No items in order</p>
                  <p className="text-[10px] mt-1">Click products or scan barcode to add</p>
                </div>
              ) : (
                orderLines.map(line => {
                  const lineTotal = line.product.price * line.qty * (1 - line.discount / 100);
                  return (
                    <div key={line.product.id} className="p-3 rounded-xl bg-white/3 border border-white/5 space-y-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] font-bold text-white truncate">{line.product.name}</p>
                          <p className="text-[9px] text-slate-500">JOD {line.product.price.toFixed(2)} × {line.qty}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs font-bold text-white">JOD {lineTotal.toFixed(2)}</p>
                          <button onClick={() => removeFromOrder(line.product.id)} className="text-red-400/60 hover:text-red-400 mt-0.5">
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={() => updateQty(line.product.id, -1)} className="w-6 h-6 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white">
                          <Minus className="w-3 h-3" />
                        </button>
                        <span className="text-xs font-bold text-white w-8 text-center">{line.qty}</span>
                        <button onClick={() => updateQty(line.product.id, 1)} className="w-6 h-6 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white">
                          <Plus className="w-3 h-3" />
                        </button>
                        <div className="flex-1" />
                        <div className="flex items-center gap-1">
                          <Tag className="w-3 h-3 text-slate-500" />
                          <select 
                            value={line.discount} onChange={e => setDiscount(line.product.id, parseInt(e.target.value))}
                            className="bg-transparent text-[10px] text-slate-400 outline-none border-none"
                          >
                            <option value={0}>No discount</option>
                            <option value={5}>5% off</option>
                            <option value={10}>10% off</option>
                            <option value={15}>15% off</option>
                            <option value={20}>20% off</option>
                            <option value={25}>25% off</option>
                            <option value={50}>50% off</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Order Totals & Payment */}
            <div className="border-t border-white/5 px-4 py-3 space-y-2 flex-shrink-0 bg-[#0a0d17]">
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Subtotal</span>
                <span className="font-mono">JOD {subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Tax (VAT)</span>
                <span className="font-mono">JOD {taxTotal.toFixed(2)}</span>
              </div>
              {roundingAdj !== 0 && (
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>Rounding (nearest {roundingStrategy} JOD)</span>
                  <span className="font-mono">{roundingAdj >= 0 ? '+' : ''}JOD {roundingAdj.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm font-black text-white border-t border-white/10 pt-2">
                <span>TOTAL</span>
                <span className="text-[#E67E22]">JOD {roundedTotal.toFixed(2)}</span>
              </div>

              {orderLines.length > 0 && (
                <button 
                  onClick={() => setShowPayment(true)}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-[#E67E22] to-[#F59E0B] text-white font-bold text-sm hover:opacity-90 transition-opacity mt-2"
                >
                  💳 Process Payment — JOD {roundedTotal.toFixed(2)}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Payment Modal */}
        <AnimatePresence>
          {showPayment && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-[#0b0f19] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-5"
              >
                <div className="flex justify-between items-center border-b border-white/5 pb-3">
                  <h3 className="text-base font-black text-white">Process Payment</h3>
                  <button onClick={() => setShowPayment(false)} className="text-slate-500 hover:text-white"><X className="w-5 h-5" /></button>
                </div>

                <div className="text-center py-3">
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Total Due</p>
                  <p className="text-4xl font-black text-[#E67E22] mt-1">JOD {roundedTotal.toFixed(2)}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{customerName} · {orderLines.length} items</p>
                </div>

                {/* Payment Method Selection */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'cash' as const, label: 'Cash', icon: Banknote, color: '#10B981' },
                    { id: 'card' as const, label: 'Card', icon: CreditCard, color: '#3B82F6' },
                    { id: 'split' as const, label: 'Split', icon: Calculator, color: '#F59E0B' },
                  ].map(method => (
                    <button
                      key={method.id}
                      onClick={() => setPaymentMethod(method.id)}
                      className={`p-3 rounded-xl border text-center transition-all ${
                        paymentMethod === method.id 
                          ? 'border-white/20 bg-white/5' 
                          : 'border-white/5 hover:border-white/10'
                      }`}
                    >
                      <method.icon className="w-5 h-5 mx-auto mb-1" style={{ color: method.color }} />
                      <span className="text-[10px] font-bold text-slate-300">{method.label}</span>
                    </button>
                  ))}
                </div>

                {paymentMethod === 'cash' && (
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-500 uppercase">Cash Tendered (JOD)</label>
                      <input 
                        type="number" step="0.01" value={cashTendered} onChange={e => setCashTendered(e.target.value)}
                        className="input-field text-lg font-mono font-bold text-center" placeholder="0.00" autoFocus
                      />
                    </div>
                    {parseFloat(cashTendered) >= roundedTotal && (
                      <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                        <p className="text-[10px] text-emerald-400 uppercase font-bold">Change Due</p>
                        <p className="text-2xl font-black text-emerald-400">JOD {(parseFloat(cashTendered) - roundedTotal).toFixed(2)}</p>
                      </div>
                    )}
                    {/* Quick Cash Buttons */}
                    <div className="grid grid-cols-4 gap-2">
                      {[roundedTotal, Math.ceil(roundedTotal), 10, 20, 50].filter((v, i, a) => a.indexOf(v) === i).slice(0, 4).map(amount => (
                        <button 
                          key={amount} 
                          onClick={() => setCashTendered(amount.toString())}
                          className="py-2 rounded-lg bg-white/5 border border-white/10 text-xs font-bold text-slate-300 hover:bg-white/10"
                        >
                          JOD {amount}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {paymentMethod === 'card' && (
                  <div className="text-center py-6 space-y-2">
                    <Smartphone className="w-10 h-10 mx-auto text-[#3B82F6] animate-pulse" />
                    <p className="text-xs text-slate-400">Waiting for card terminal...</p>
                    <p className="text-[10px] text-slate-500">Tap, insert, or swipe card on terminal device</p>
                  </div>
                )}

                <button 
                  onClick={processPayment}
                  disabled={paymentMethod === 'cash' && parseFloat(cashTendered) < roundedTotal}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-bold text-sm hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <CheckCircle className="w-4 h-4 inline mr-2" />
                  Confirm Payment
                </button>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // ── Receipt View ──
  if (posView === 'receipt' && lastReceipt) {
    return (
      <div className="space-y-6">
        <div className="page-header">
          <div>
            <h1 className="page-title text-white">Payment Confirmed ✓</h1>
            <p className="page-subtitle">Receipt {lastReceipt.id} processed successfully.</p>
          </div>
          <button onClick={() => setPosView('terminal')} className="btn-primary flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> New Sale
          </button>
        </div>

        <div className="max-w-md mx-auto">
          <div className="glass-card p-6 space-y-4">
            <div className="text-center border-b border-white/10 pb-4">
              <p className="text-lg font-black text-white">CYCOM ERP</p>
              <p className="text-[10px] text-slate-500">{activeCompany.name}</p>
              <p className="text-[10px] text-slate-500">{storeName}</p>
              <p className="text-[10px] text-slate-500 font-mono mt-1">{lastReceipt.date}</p>
              <p className="text-[10px] text-slate-500 font-mono">Receipt: {lastReceipt.id}</p>
            </div>

            <div className="space-y-2">
              {lastReceipt.lines.map((line, i) => (
                <div key={i} className="flex justify-between text-xs">
                  <span className="text-slate-300">{line.qty}× {line.product.name}</span>
                  <span className="font-mono text-white">JOD {(line.product.price * line.qty * (1 - line.discount / 100)).toFixed(2)}</span>
                </div>
              ))}
            </div>

            <div className="border-t border-white/10 pt-3 space-y-1">
              <div className="flex justify-between text-xs text-slate-400">
                <span>Tax (VAT)</span>
                <span className="font-mono">JOD {lastReceipt.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm font-black text-white">
                <span>TOTAL</span>
                <span className="text-[#E67E22]">JOD {lastReceipt.total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-400">
                <span>Payment</span>
                <span>{lastReceipt.payment}</span>
              </div>
              {lastReceipt.change > 0 && (
                <div className="flex justify-between text-xs text-emerald-400 font-bold">
                  <span>Change</span>
                  <span>JOD {lastReceipt.change.toFixed(2)}</span>
                </div>
              )}
            </div>

            <div className="text-center border-t border-white/10 pt-4 text-[10px] text-slate-500">
              <p>Thank you for shopping at Cycom!</p>
              <p className="mt-1">Customer: {lastReceipt.customer}</p>
            </div>

            <button className="w-full py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-slate-300 hover:bg-white/10 flex items-center justify-center gap-2">
              <Printer className="w-3.5 h-3.5" /> Print Receipt
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Orders & Session Management View (Default / Session Closed) ──
  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Point of Sale (POS) Station</h1>
          <p className="page-subtitle">Manage retail sessions, cash registers, advance orders, and pledge records for {storeName}.</p>
        </div>
        <div className="flex gap-3">
          {sessionOpen && (
            <button onClick={() => setPosView('terminal')} className="btn-primary flex items-center gap-2">
              <ShoppingCart className="w-4 h-4" /> Open Terminal
            </button>
          )}
          <button 
            onClick={() => { setSessionOpen(!sessionOpen); if (!sessionOpen) setPosView('terminal'); }}
            className={`btn-${sessionOpen ? 'secondary' : 'primary'} flex items-center gap-2`}
          >
            {sessionOpen ? <><Lock className="w-4 h-4 text-red-400" /> Close Session</> : <><Unlock className="w-4 h-4 text-emerald-400" /> Open Session</>}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Register Status</span>
            <p className="text-xl font-black text-white flex items-center gap-2 mt-1">
              <span className={`w-2.5 h-2.5 rounded-full ${sessionOpen ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
              {sessionOpen ? 'OPEN' : 'LOCKED'}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-white/5 text-slate-400"><ShoppingCart className="w-5 h-5" /></div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Cash Float</span>
            <p className="text-2xl font-black text-[#10B981]">JOD {cashFloat.toFixed(2)}</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400"><Banknote className="w-5 h-5" /></div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Advance Deposits</span>
            <p className="text-2xl font-black text-[#5DADE2]">JOD {orders.filter(o => o.type === 'Advance Order' && o.status === 'Pending').reduce((acc, c) => acc + c.deposit, 0)}</p>
          </div>
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400"><Calendar className="w-5 h-5" /></div>
        </div>
        <div className="stat-card flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Products in Catalog</span>
            <p className="text-2xl font-black text-[#F59E0B]">{PRODUCTS.length}</p>
          </div>
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400"><Package className="w-5 h-5" /></div>
        </div>
      </div>

      {sessionsLoading && <div style={{ padding: '2rem', color: '#ccc' }}>Loading...</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cash Drawer */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">Cash Drawer Log</h2>
          </div>
          {sessionOpen ? (
            <div className="space-y-4">
              <div className="space-y-2 max-h-[160px] overflow-y-auto">
                {cashMoves.map(move => (
                  <div key={move.id} className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-white/3 border border-white/5">
                    <div>
                      <div className="flex items-center gap-1.5 font-bold">
                        {move.type === 'Cash-In' ? <ArrowDownRight className="w-3.5 h-3.5 text-emerald-400" /> : <ArrowUpRight className="w-3.5 h-3.5 text-red-400" />}
                        <span className="text-white">{move.reason}</span>
                      </div>
                      <span className="text-[9px] text-slate-500 font-mono">{move.timestamp}</span>
                    </div>
                    <span className={`font-bold font-mono ${move.type === 'Cash-In' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {move.type === 'Cash-In' ? '+' : '-'}JOD {move.amount.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
              <form onSubmit={handleCashMoveSubmit} className="space-y-2 text-xs">
                <div className="grid grid-cols-3 gap-2">
                  <select value={moveType} onChange={e => setMoveType(e.target.value as any)} className="input-field py-1">
                    <option value="Cash-In">In (Add)</option>
                    <option value="Cash-Out">Out (Pay)</option>
                  </select>
                  <input type="number" required placeholder="Amount" value={moveAmt} onChange={e => setMoveAmt(e.target.value)} className="input-field py-1 font-mono col-span-2" />
                </div>
                <input type="text" required placeholder="Reason..." value={moveReason} onChange={e => setMoveReason(e.target.value)} className="input-field py-1" />
                <button type="submit" className="btn-secondary w-full py-1.5">Record Cash Move</button>
              </form>
            </div>
          ) : (
            <div className="py-10 text-center text-slate-500 italic text-xs">Session locked. Open session to manage cash.</div>
          )}
        </div>

        {/* Orders */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-3">Advance & Pledge Registry</h2>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead><tr><th>ID</th><th>Customer</th><th>Type</th><th>Total</th><th>Deposit</th><th>Deadline</th><th>Status</th><th className="text-right">Action</th></tr></thead>
                <tbody>
                  {orders.map(ord => (
                    <tr key={ord.id}>
                      <td className="font-mono text-xs">{ord.id}</td>
                      <td className="font-bold text-slate-300">{ord.customerName}</td>
                      <td><span className={`badge text-[9px] ${ord.type === 'Advance Order' ? 'badge-cyan' : 'badge-orange'}`}>{ord.type}</span></td>
                      <td className="font-bold">JOD {ord.total}</td>
                      <td className="text-emerald-400">JOD {ord.deposit}</td>
                      <td>{ord.deadlineDate}</td>
                      <td><span className={`badge text-[9px] ${ord.status === 'Fulfilled' ? 'badge-green' : ord.status === 'Overdue' ? 'badge-red' : 'badge-yellow'}`}>{ord.status}</span></td>
                      <td className="text-right">{ord.status === 'Pending' && (
                        <button onClick={() => setFulfilledIds(prev => [...prev, ord.id])} className="p-1 px-2 text-[10px] font-bold rounded bg-emerald-500/10 border border-emerald-500/25 text-[#10B981]">Fulfill</button>
                      )}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="glass-card p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 border-b border-white/5 pb-2">New Advance / Pledge</h3>
            <form onSubmit={handleCreateOrder} className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-3">
                <div className="space-y-1"><label className="text-[10px] font-bold text-slate-500 uppercase">Customer</label><input type="text" required placeholder="Customer name" value={orderCust} onChange={e => setOrderCust(e.target.value)} className="input-field" /></div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1"><label className="text-[10px] font-bold text-slate-500 uppercase">Type</label><select value={orderType} onChange={e => setOrderType(e.target.value as any)} className="input-field"><option value="Advance Order">Advance</option><option value="Pledge Order">Pledge</option></select></div>
                  <div className="space-y-1"><label className="text-[10px] font-bold text-slate-500 uppercase">Total (JOD)</label><input type="number" required placeholder="500" value={orderTotal} onChange={e => setOrderTotal(e.target.value)} className="input-field font-mono" /></div>
                </div>
              </div>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1"><label className="text-[10px] font-bold text-slate-500 uppercase">Deposit</label><input type="number" disabled={orderType === 'Pledge Order'} placeholder={orderType === 'Pledge Order' ? '0' : '150'} value={orderType === 'Pledge Order' ? '' : orderDeposit} onChange={e => setOrderDeposit(e.target.value)} className="input-field disabled:opacity-50 font-mono" /></div>
                  <div className="space-y-1"><label className="text-[10px] font-bold text-slate-500 uppercase">Due Date</label><input type="date" required value={orderDeadline} onChange={e => setOrderDeadline(e.target.value)} className="input-field" /></div>
                </div>
                <button type="submit" className="btn-primary w-full py-2 mt-1">Create POS Record</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
