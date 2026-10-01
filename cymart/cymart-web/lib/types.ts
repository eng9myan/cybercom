export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "athlete";
export type GoalType = "lose" | "maintain" | "gain";
export type Strictness = "strict" | "balanced" | "coach";

export interface DietRegime {
  code: string;
  name_en: string;
  name_ar: string;
  description_en: string;
  max_item_carbs_g: string | null;
}

export interface DietProfile {
  id: string;
  sex: "male" | "female";
  age: number;
  height_cm: string;
  weight_kg: string;
  activity_level: ActivityLevel;
  goal_type: GoalType;
  target_weight_kg: string | null;
  weekly_pace_kg: string;
  strictness: Strictness;
  allergies: string[];
  medical_conditions: string[];
  is_pregnant: boolean;
  is_breastfeeding: boolean;
  regimes: DietRegime[];
  is_active: boolean;
}

export interface DietProfileInput {
  sex: "male" | "female";
  age: number;
  height_cm: string;
  weight_kg: string;
  activity_level: ActivityLevel;
  goal_type: GoalType;
  weekly_pace_kg: string;
  strictness: Strictness;
  allergies: string[];
  medical_conditions: string[];
  is_pregnant: boolean;
  is_breastfeeding: boolean;
  regime_codes: string[];
}

export interface DietPlan {
  id: string;
  bmr: number;
  tdee: number;
  daily_calories: number;
  min_daily_calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  per_meal: { breakfast: number; lunch: number; dinner: number; snack: number };
  valid_from: string;
  review_on: string | null;
  is_active: boolean;
}

export interface TodayStatus {
  date: string;
  daily_calories: number;
  consumed_calories: number;
  remaining_calories: number;
  on_track: boolean;
  protein_g_target: number;
  protein_g_consumed: number;
  off_plan_overrides: number;
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name_snapshot: string;
  quantity: string;
  unit_price: string;
  item_discount: string;
  notes: string;
}

export interface Cart {
  id: string;
  customer_id: string;
  store_id: string | null;
  tenant_id: string | null;
  status: "active" | "checked_out" | "abandoned";
  order_id: string | null;
  items: CartItem[];
  created_at: string;
  updated_at: string;
}

export interface AgentToolCall {
  name: string;
  arguments: Record<string, unknown>;
  output: Record<string, unknown>;
}

export interface AgentReply {
  reply: string;
  tool_calls: AgentToolCall[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  toolCalls?: AgentToolCall[];
}

export interface ReplenishItem {
  product_id: string;
  product_name: string;
  quantity: string | null;
  unit: string;
  predicted_runout_date: string | null;
}

export interface TrackingEvent {
  status: string;
  note: string;
  occurred_at: string;
}

export interface OrderTracking {
  assignment_id: string;
  status: string;
  driver_name: string;
  timeline: TrackingEvent[];
}

export interface ApiErrorBody {
  detail?: string;
  code?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  status: number;
  body: ApiErrorBody;
  constructor(status: number, body: ApiErrorBody) {
    super(body.detail || `Request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}
