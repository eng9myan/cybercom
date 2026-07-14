'use client';

import React from 'react';
import { Building2, CornerDownRight, ArrowUpRight } from 'lucide-react';
import { useCycomList, m2oName, type Many2One } from '@/lib/cycomModels';
import { LoadingCard, ErrorCard, EmptyCard } from '@/components/CycomEmptyStates';

type CycomDept = {
  id: number;
  name?: string;
  manager_id?: Many2One;
  parent_id?: Many2One;
  total_employee?: number;
  total_employee_fnct?: number;
  child_ids?: number[];
  member_ids?: number[];
};

type DeptNode = {
  id: number;
  name: string;
  head: string;
  directEmployees: number;
  childEmployees: number;
  totalEmployees: number;
  parentId: number | null;
  subDepartments: DeptNode[];
};

function buildTree(flat: CycomDept[]): DeptNode[] {
  const nodes: Record<number, DeptNode> = {};
  for (const d of flat) {
    nodes[d.id] = {
      id: d.id,
      name: d.name || `Department ${d.id}`,
      head: m2oName(d.manager_id, 'Unassigned'),
      directEmployees: d.member_ids?.length ?? 0,
      childEmployees: 0,
      totalEmployees: d.total_employee ?? (d.member_ids?.length ?? 0),
      parentId: d.parent_id ? d.parent_id[0] : null,
      subDepartments: [],
    };
  }
  const roots: DeptNode[] = [];
  for (const node of Object.values(nodes)) {
    if (node.parentId && nodes[node.parentId]) {
      nodes[node.parentId].subDepartments.push(node);
    } else {
      roots.push(node);
    }
  }
  // child employee rollup
  function rollUp(n: DeptNode): number {
    n.childEmployees = n.subDepartments.reduce((acc, c) => acc + rollUp(c), 0);
    return n.totalEmployees;
  }
  roots.forEach(rollUp);
  return roots;
}

export default function DepartmentHierarchy() {
  const { rows: flat, loading, error } = useCycomList<CycomDept, CycomDept>(
    'hr.department',
    [],
    ['name', 'manager_id', 'parent_id', 'total_employee', 'child_ids', 'member_ids'],
    (r) => r,
    { limit: 500, order: 'parent_id asc, name asc' },
  );

  const tree = !loading && !error ? buildTree(flat) : [];
  const totalDepts = flat.length;
  const totalEmps = flat.reduce((acc, d) => acc + (d.member_ids?.length ?? 0), 0);

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title text-white">Department Hierarchy</h1>
          <p className="page-subtitle">Understand company structure and dynamic child employee metrics propagated down departments (hr_department_child_employee_count).</p>
        </div>
      </div>

      {loading && <LoadingCard label="Loading departments…" />}
      {error && <ErrorCard error={error} />}
      {!loading && !error && tree.length === 0 && <EmptyCard label="No departments configured. Run the HR Structure wizard." />}

      {!loading && !error && tree.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="glass-card p-6 lg:col-span-2 space-y-6">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Organizational Tree</h2>
            <div className="space-y-4">
              {tree.map((dept) => (
                <div key={dept.id} className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20">
                    <div className="flex items-center gap-3">
                      <Building2 className="w-5 h-5 text-cyan-400" />
                      <div>
                        <h3 className="text-base font-bold text-white">{dept.name}</h3>
                        <p className="text-xs text-slate-400">Head: {dept.head}</p>
                      </div>
                    </div>
                    <div className="flex gap-4 items-center">
                      <div className="text-right">
                        <span className="text-xs text-slate-500 block">Direct / Child</span>
                        <span className="text-sm font-bold text-slate-200">{dept.directEmployees} / {dept.childEmployees}</span>
                      </div>
                      <span className="badge badge-cyan">{dept.totalEmployees} Total</span>
                    </div>
                  </div>

                  {dept.subDepartments.length > 0 && (
                    <div className="pl-6 space-y-4 border-l border-white/5">
                      {dept.subDepartments.map((sub) => (
                        <div key={sub.id} className="space-y-4">
                          <div className="flex items-center justify-between p-3.5 rounded-lg bg-white/5 border border-white/5">
                            <div className="flex items-center gap-2">
                              <CornerDownRight className="w-4 h-4 text-slate-500" />
                              <div>
                                <h4 className="text-sm font-bold text-slate-200">{sub.name}</h4>
                                <p className="text-xs text-slate-400">Head: {sub.head}</p>
                              </div>
                            </div>
                            <div className="flex gap-4 items-center">
                              <div className="text-right">
                                <span className="text-[10px] text-slate-500 block">Direct / Child</span>
                                <span className="text-xs font-semibold text-slate-300">{sub.directEmployees} / {sub.childEmployees}</span>
                              </div>
                              <span className="badge badge-purple">{sub.totalEmployees} Total</span>
                            </div>
                          </div>
                          {sub.subDepartments.length > 0 && (
                            <div className="pl-8 space-y-2 border-l border-white/5">
                              {sub.subDepartments.map((sub2) => (
                                <div key={sub2.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:border-[#E67E22]/20 transition-colors">
                                  <div className="flex items-center gap-2">
                                    <CornerDownRight className="w-4 h-4 text-slate-600" />
                                    <div>
                                      <h5 className="text-xs font-bold text-slate-300">{sub2.name}</h5>
                                      <p className="text-[10px] text-slate-500">Head: {sub2.head}</p>
                                    </div>
                                  </div>
                                  <div className="flex gap-4 items-center">
                                    <div className="text-right">
                                      <span className="text-[10px] text-slate-500 block">Direct</span>
                                      <span className="text-xs font-semibold text-slate-400">{sub2.directEmployees}</span>
                                    </div>
                                    <span className="badge badge-orange">{sub2.totalEmployees} Total</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <div className="glass-card p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Rollup Stats</h2>
              <div className="space-y-4 text-sm">
                <div className="flex justify-between items-center pb-3 border-b border-white/5">
                  <span className="text-slate-400">Total Departments</span>
                  <span className="text-white font-bold">{totalDepts}</span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-white/5">
                  <span className="text-slate-400">Total Employees</span>
                  <span className="text-white font-bold">{totalEmps}</span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-white/5">
                  <span className="text-slate-400">Root Departments</span>
                  <span className="text-white font-bold">{tree.length}</span>
                </div>
              </div>
            </div>

            <div className="glass-card p-6 border-cyan-500/20">
              <h3 className="text-sm font-bold text-white mb-2">Automated Count Logic</h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Cycom calculates department headcount dynamically by summarizing the active child departments recursively. The Next.js framework exposes this hierarchy using cached database summaries.
              </p>
              <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-semibold cursor-pointer hover:underline">
                Read Cycom Module Specification <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
