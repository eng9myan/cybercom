"use client";

import Link from "next/link";
import {
  Building2, Stethoscope, ShoppingCart, BarChart3, Pill,
  FlaskConical, Scan, ArrowUpRight, Users, DollarSign,
  ExternalLink, Globe,
} from "lucide-react";

const PRODUCTS = [
  {
    id: "cymed-hospital", name: "CyMed Hospital", icon: Building2,
    color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20",
    category: "Healthcare", status: "GA",
    editions: [
      { name: "Hospital Core", price: 2500, customers: 4 },
      { name: "Hospital Advanced", price: 4500, customers: 6 },
      { name: "Hospital Enterprise", price: null, customers: 2 },
    ],
    totalCustomers: 12, totalMRR: 52400,
    demoUrl: "https://cymed.cy-com.com/hospital",
    pageUrl: "/en/products/cymed-hospital",
  },
  {
    id: "cymed-clinic", name: "CyMed Clinic", icon: Stethoscope,
    color: "text-teal-400", bg: "bg-teal-500/10", border: "border-teal-500/20",
    category: "Healthcare", status: "GA",
    editions: [
      { name: "Clinic Starter", price: 299, customers: 5 },
      { name: "Clinic Professional", price: 599, customers: 8 },
      { name: "Clinic Enterprise", price: null, customers: 2 },
    ],
    totalCustomers: 15, totalMRR: 21300,
    demoUrl: "https://cymed.cy-com.com/clinic",
    pageUrl: "/en/products/cymed-clinic",
  },
  {
    id: "cymed-pharmacy", name: "CyMed Pharmacy", icon: Pill,
    color: "text-violet-400", bg: "bg-violet-500/10", border: "border-violet-500/20",
    category: "Healthcare", status: "GA",
    editions: [
      { name: "Pharmacy Core", price: 199, customers: 5 },
      { name: "Pharmacy Clinical", price: 399, customers: 6 },
    ],
    totalCustomers: 11, totalMRR: 8930,
    demoUrl: "https://cymed.cy-com.com/pharmacy",
    pageUrl: "/en/products/cymed-pharmacy",
  },
  {
    id: "cymed-laboratory", name: "CyMed Laboratory", icon: FlaskConical,
    color: "text-cyan-400", bg: "bg-cyan-500/10", border: "border-cyan-500/20",
    category: "Healthcare", status: "GA",
    editions: [
      { name: "Lab Core", price: 299, customers: 2 },
      { name: "Lab Full", price: 549, customers: 3 },
    ],
    totalCustomers: 5, totalMRR: 3950,
    demoUrl: "https://cymed.cy-com.com/laboratory",
    pageUrl: "/en/products/cymed-laboratory",
  },
  {
    id: "cymed-imaging", name: "CyMed Imaging", icon: Scan,
    color: "text-sky-400", bg: "bg-sky-500/10", border: "border-sky-500/20",
    category: "Healthcare", status: "GA",
    editions: [
      { name: "Imaging Core", price: 399, customers: 1 },
      { name: "Imaging Advanced", price: 799, customers: 2 },
    ],
    totalCustomers: 3, totalMRR: 1950,
    demoUrl: "https://cymed.cy-com.com/imaging",
    pageUrl: "/en/products/cymed-imaging",
  },
  {
    id: "cyshop", name: "CyShop", icon: ShoppingCart,
    color: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/20",
    category: "Retail", status: "GA",
    editions: [
      { name: "Starter", price: 99, customers: 2 },
      { name: "Business", price: 299, customers: 5 },
      { name: "Enterprise", price: null, customers: 1 },
    ],
    totalCustomers: 8, totalMRR: 14800,
    demoUrl: "https://cyshop.cy-com.com",
    pageUrl: "/en/products/cyshop",
  },
  {
    id: "cycom-erp", name: "CyCom ERP", icon: BarChart3,
    color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20",
    category: "ERP", status: "GA",
    editions: [
      { name: "Business", price: 999, customers: 8 },
      { name: "Enterprise", price: 2499, customers: 10 },
      { name: "Healthcare ERP", price: null, customers: 4 },
    ],
    totalCustomers: 22, totalMRR: 43900,
    demoUrl: "https://health.cy-com.com",
    pageUrl: "/en/products/cycom",
  },
];

export default function AdminProductsPage() {
  const grandMRR = PRODUCTS.reduce((s, p) => s + p.totalMRR, 0);
  const grandCustomers = PRODUCTS.reduce((s, p) => s + p.totalCustomers, 0);

  return (
    <div>
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-heading font-semibold text-white mb-1">Product Catalog</h1>
          <p className="text-sm text-cy-gray-400">7 products · {grandCustomers} subscriptions · ${grandMRR.toLocaleString()}/mo total MRR</p>
        </div>
      </div>

      <div className="space-y-4">
        {PRODUCTS.map((product) => {
          const Icon = product.icon;
          return (
            <div key={product.id} className="glass-card rounded-xl overflow-hidden">
              {/* Header */}
              <div className="p-5 flex items-start gap-4">
                <div className={`w-12 h-12 rounded-xl ${product.bg} border ${product.border} flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-6 h-6 ${product.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-heading font-semibold text-white">{product.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">{product.status}</span>
                    <span className="text-xs text-cy-gray-500">{product.category}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1.5 text-cy-gray-300">
                      <Users className="w-3.5 h-3.5 text-cy-gray-500" />
                      {product.totalCustomers} customers
                    </div>
                    <div className="flex items-center gap-1.5 text-cy-gray-300">
                      <DollarSign className="w-3.5 h-3.5 text-cy-gray-500" />
                      ${product.totalMRR.toLocaleString()}/mo MRR
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <a
                    href={product.demoUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-cy-gray-300 border border-cy-glass-border hover:border-cy-glass-bg-hover transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" /> Demo
                  </a>
                  <Link
                    href={product.pageUrl}
                    target="_blank"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-cy-gray-300 border border-cy-glass-border hover:border-cy-glass-bg-hover transition-colors"
                  >
                    <Globe className="w-3 h-3" /> Page
                  </Link>
                </div>
              </div>

              {/* Edition breakdown */}
              <div className="border-t border-cy-glass-border overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-cy-glass-border/50">
                      {["Edition", "Price", "Customers", "MRR"].map((h) => (
                        <th key={h} className="px-5 py-2.5 text-left text-xs font-medium text-cy-gray-500">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {product.editions.map((ed) => (
                      <tr key={ed.name} className="border-b border-cy-glass-border/30 last:border-0 hover:bg-cy-glass-border/10 transition-colors">
                        <td className="px-5 py-3 text-white font-medium">{ed.name}</td>
                        <td className="px-5 py-3 text-cy-gray-300">
                          {ed.price !== null ? `$${ed.price.toLocaleString()}/mo` : "Custom"}
                        </td>
                        <td className="px-5 py-3 text-cy-gray-300">{ed.customers}</td>
                        <td className="px-5 py-3">
                          {ed.price !== null
                            ? <span className="font-semibold text-emerald-400">${(ed.price * 0.8 * ed.customers).toLocaleString()}</span>
                            : <span className="text-cy-gray-400 text-xs">Custom pricing</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
