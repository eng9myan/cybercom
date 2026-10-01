"use client";

import { useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useCreateDietProfile, useDietPlan, useDietProfile, useRegimes } from "@/lib/queries";
import type { ActivityLevel, DietProfileInput, GoalType, Strictness } from "@/lib/types";
import { Button, Card, Spinner } from "./ui";

const ACTIVITY_LEVELS: { value: ActivityLevel; label: string }[] = [
  { value: "sedentary", label: "Sedentary — little to no exercise" },
  { value: "light", label: "Light — 1-3 days/week" },
  { value: "moderate", label: "Moderate — 3-5 days/week" },
  { value: "active", label: "Very active — 6-7 days/week" },
  { value: "athlete", label: "Extra active — training twice a day" },
];

const GOALS: { value: GoalType; label: string }[] = [
  { value: "lose", label: "Lose weight" },
  { value: "maintain", label: "Maintain" },
  { value: "gain", label: "Gain / build muscle" },
];

const STRICTNESS: { value: Strictness; label: string; hint: string }[] = [
  { value: "strict", label: "Strict", hint: "Block anything off-plan" },
  { value: "balanced", label: "Balanced", hint: "Warn, let me override" },
  { value: "coach", label: "Coach", hint: "Never block, just advise" },
];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[13px] font-medium" style={{ color: "var(--ink-2)" }}>
        {label}
      </span>
      {children}
    </label>
  );
}

const inputStyle: React.CSSProperties = {
  background: "var(--panel-2)",
  borderColor: "var(--line)",
  color: "var(--ink)",
};

export function OnboardingForm() {
  const { data: existingProfile, isLoading: loadingProfile } = useDietProfile();
  const { data: regimes } = useRegimes();
  const { data: plan } = useDietPlan(!!existingProfile);
  const createProfile = useCreateDietProfile();

  const [form, setForm] = useState<DietProfileInput>({
    sex: "male",
    age: 30,
    height_cm: "175",
    weight_kg: "80",
    activity_level: "sedentary",
    goal_type: "lose",
    weekly_pace_kg: "0.5",
    strictness: "balanced",
    allergies: [],
    medical_conditions: [],
    is_pregnant: false,
    is_breastfeeding: false,
    regime_codes: [],
  });
  const [allergiesText, setAllergiesText] = useState("");

  if (loadingProfile) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size={24} />
      </div>
    );
  }

  if (existingProfile && plan) {
    return (
      <div className="flex flex-col gap-4">
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={18} style={{ color: "var(--teal)" }} />
            <h2>Your plan</h2>
          </div>
          <div className="text-[28px] font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            {plan.daily_calories} <span className="text-[15px] font-normal" style={{ color: "var(--ink-2)" }}>kcal / day</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[
              ["Protein", `${plan.protein_g}g`],
              ["Carbs", `${plan.carbs_g}g`],
              ["Fat", `${plan.fat_g}g`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-[10px] p-2.5 text-center" style={{ background: "var(--panel-2)" }}>
                <div className="text-[11px]" style={{ color: "var(--ink-3)" }}>
                  {label}
                </div>
                <div className="text-[15px] font-medium">{value}</div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {existingProfile.regimes.map((r) => (
              <span key={r.code} className="rounded-full px-2.5 py-1 text-[12px]" style={{ background: "var(--violet-bg)", color: "var(--violet)" }}>
                {r.name_en}
              </span>
            ))}
          </div>
        </Card>
        <p className="text-[13px]" style={{ color: "var(--ink-3)" }}>
          Head to the order screen and Diet Shield will guard every order from here.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        createProfile.mutate({
          ...form,
          allergies: allergiesText
            .split(",")
            .map((s) => s.trim().toLowerCase())
            .filter(Boolean),
        });
      }}
      className="flex flex-col gap-5"
    >
      <div>
        <h1 className="text-[22px]">Let&apos;s build your plan</h1>
        <p className="mt-1 text-[13.5px]" style={{ color: "var(--ink-2)" }}>
          Two minutes. Diet Shield will use this to guard every order.
        </p>
      </div>

      <Card className="grid grid-cols-2 gap-3">
        <Field label="Sex">
          <select
            className="rounded-[8px] border px-2.5 py-2 text-[14px]"
            style={inputStyle}
            value={form.sex}
            onChange={(e) => setForm({ ...form, sex: e.target.value as "male" | "female" })}
          >
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </Field>
        <Field label="Age">
          <input
            type="number"
            min={13}
            max={120}
            className="rounded-[8px] border px-2.5 py-2 text-[14px]"
            style={inputStyle}
            value={form.age}
            onChange={(e) => setForm({ ...form, age: Number(e.target.value) })}
          />
        </Field>
        <Field label="Height (cm)">
          <input
            type="number"
            className="rounded-[8px] border px-2.5 py-2 text-[14px]"
            style={inputStyle}
            value={form.height_cm}
            onChange={(e) => setForm({ ...form, height_cm: e.target.value })}
          />
        </Field>
        <Field label="Weight (kg)">
          <input
            type="number"
            className="rounded-[8px] border px-2.5 py-2 text-[14px]"
            style={inputStyle}
            value={form.weight_kg}
            onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
          />
        </Field>
      </Card>

      <Card className="flex flex-col gap-3">
        <Field label="Activity level">
          <select
            className="rounded-[8px] border px-2.5 py-2 text-[14px]"
            style={inputStyle}
            value={form.activity_level}
            onChange={(e) => setForm({ ...form, activity_level: e.target.value as ActivityLevel })}
          >
            {ACTIVITY_LEVELS.map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Goal">
          <div className="flex gap-2">
            {GOALS.map((g) => (
              <button
                type="button"
                key={g.value}
                onClick={() => setForm({ ...form, goal_type: g.value })}
                className="flex-1 rounded-[8px] border px-2 py-2 text-[13px] transition"
                style={{
                  borderColor: form.goal_type === g.value ? "var(--teal)" : "var(--line)",
                  background: form.goal_type === g.value ? "var(--teal-bg)" : "var(--panel-2)",
                  color: form.goal_type === g.value ? "var(--teal)" : "var(--ink-2)",
                }}
              >
                {g.label}
              </button>
            ))}
          </div>
        </Field>
        {form.goal_type !== "maintain" && (
          <Field label="Pace (kg/week)">
            <input
              type="number"
              step="0.25"
              min="0.25"
              max="1"
              className="rounded-[8px] border px-2.5 py-2 text-[14px]"
              style={inputStyle}
              value={form.weekly_pace_kg}
              onChange={(e) => setForm({ ...form, weekly_pace_kg: e.target.value })}
            />
          </Field>
        )}
      </Card>

      <Card className="flex flex-col gap-2.5">
        <span className="text-[13px] font-medium" style={{ color: "var(--ink-2)" }}>
          Diet regime (optional, pick any)
        </span>
        <div className="flex flex-wrap gap-2">
          {(regimes || []).map((r) => {
            const active = form.regime_codes.includes(r.code);
            return (
              <button
                type="button"
                key={r.code}
                onClick={() =>
                  setForm({
                    ...form,
                    regime_codes: active
                      ? form.regime_codes.filter((c) => c !== r.code)
                      : [...form.regime_codes, r.code],
                  })
                }
                className="rounded-full border px-3 py-1.5 text-[12.5px] transition"
                style={{
                  borderColor: active ? "var(--violet)" : "var(--line-2)",
                  background: active ? "var(--violet-bg)" : "transparent",
                  color: active ? "var(--violet)" : "var(--ink-2)",
                }}
              >
                {r.name_en}
              </button>
            );
          })}
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <Field label="Allergies (comma-separated — always a hard block)">
          <input
            className="rounded-[8px] border px-2.5 py-2 text-[14px]"
            style={inputStyle}
            placeholder="peanuts, shellfish"
            value={allergiesText}
            onChange={(e) => setAllergiesText(e.target.value)}
          />
        </Field>
        <Field label="How strict should Diet Shield be?">
          <div className="grid grid-cols-3 gap-2">
            {STRICTNESS.map((s) => (
              <button
                type="button"
                key={s.value}
                onClick={() => setForm({ ...form, strictness: s.value })}
                className="rounded-[8px] border p-2 text-left text-[12.5px] transition"
                style={{
                  borderColor: form.strictness === s.value ? "var(--teal)" : "var(--line)",
                  background: form.strictness === s.value ? "var(--teal-bg)" : "var(--panel-2)",
                }}
              >
                <div className="font-medium" style={{ color: form.strictness === s.value ? "var(--teal)" : "var(--ink)" }}>
                  {s.label}
                </div>
                <div style={{ color: "var(--ink-3)" }}>{s.hint}</div>
              </button>
            ))}
          </div>
        </Field>
      </Card>

      {createProfile.isError && (
        <p className="text-[13px]" style={{ color: "var(--coral)" }}>
          Couldn&apos;t build your plan. Check your numbers and try again.
        </p>
      )}

      <Button type="submit" variant="primary" disabled={createProfile.isPending} className="justify-center py-3">
        {createProfile.isPending ? <Loader2 size={16} className="animate-spin" /> : "Build my plan"}
      </Button>
    </form>
  );
}
