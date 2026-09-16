export type Student = {
  id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  student_number?: string;
  year_level: number;
  enrolment_status: string;
  email?: string;
};

export type ClassSection = {
  id: string;
  name: string;
  subject?: string;
  year_level: number;
  teacher_name?: string;
  room?: string;
};

export type RollCall = {
  id: string;
  class_section: string;
  class_section_name?: string;
  date: string;
  period_label?: string;
  present_count?: number;
  absent_count?: number;
};

export type Assessment = {
  id: string;
  class_section: string;
  class_section_name?: string;
  name: string;
  assessment_type: string;
  max_score: string;
  curriculum_code?: string;
  due_date?: string | null;
};

export type Grade = {
  id: string;
  assessment: string;
  student: string;
  student_name?: string;
  score: string | null;
  achievement_level?: string;
  comment?: string;
  percentage?: number | null;
};

export type Citation = { code: string; learning_area: string; year_level: number };

export type TutorResult = {
  answer: string;
  grounded: boolean;
  citations: Citation[];
  adaptations: string[];
  agent_key: string;
  reviewed_by_human: boolean;
};

export type GeneratedArtifact = {
  id: string;
  artifact_type: string;
  title: string;
  subject?: string;
  year_level?: number | null;
  curriculum_codes?: string;
  content: Record<string, unknown>;
  status: string;
  reviewed_by?: string;
  llm_generated?: boolean;
};

export type IntegrityReview = {
  id: string;
  title: string;
  risk_band: string;
  decision: string;
  decided_by?: string;
  signals: Record<string, unknown>;
  draft_versions: number;
  edit_span_minutes: number;
  disclosed_ai_use: boolean;
};

export type Application = {
  id: string;
  applicant_first_name: string;
  applicant_last_name: string;
  year_level_applying: number;
  status: string;
  guardian_name?: string;
  enrolled_student_id?: string | null;
};

export type Invoice = {
  id: string;
  student: string;
  description?: string;
  amount: string;
  currency?: string;
  status: string;
  paid_total?: string;
  balance?: string;
  due_date?: string | null;
};

export type Course = {
  id: string;
  name: string;
  subject?: string;
  year_level: number;
  is_published: boolean;
  lesson_count?: number;
};

export type LearnerProfile = {
  id: string;
  student: string;
  eald_level?: string;
  first_language?: string;
  is_neurodivergent: boolean;
  reading_level?: string;
  accommodations?: string;
};

export type BehaviourIncident = {
  id: string;
  student: string;
  date: string;
  category: string;
  description?: string;
  resolved: boolean;
};

export type ReportCard = {
  id: string;
  student: string;
  student_name?: string;
  term: string;
  status: string;
  published_on?: string | null;
  general_comment?: string;
};

export type ReportCardDocument = {
  id: string;
  version: number;
  content_hash: string;
  verified: boolean;
  published_by?: string;
  acknowledged_by?: string;
  acknowledged_at?: string | null;
};

export type TransportZone = { id: string; name: string; base_fee: string; min_km: string; max_km: string };
export type Bus = { id: string; identifier: string; capacity: number; driver_name?: string; supervisor_name?: string; seats_available?: number };
export type TransportSubscription = {
  id: string; student: string; zone: string; trip_type: string;
  fee_amount: string; status: string; assigned_bus?: string | null;
};

export type FeePlan = { id: string; name: string; schedule_type: string; installments_count: number; upfront_discount_percent: string; late_fee_percent: string };
export type Installment = { id: string; installment_no: number; due_date?: string | null; amount_due: string; status: string; paid_total?: string; balance?: string };
export type StudentBill = {
  id: string; student: string; plan?: string | null; status: string;
  total_amount?: string; paid_amount?: string; balance?: string;
  line_items?: { id: string; category: string; description?: string; amount: string }[];
  installments?: Installment[];
};

export type SchoolProfile = {
  id: string;
  name: string;
  short_name?: string;
  address?: string;
  suburb?: string;
  state?: string;
  postcode?: string;
  principal_name?: string;
  contact_email?: string;
  contact_phone?: string;
  has_logo: boolean;
  logo_content_type?: string;
};

export type SocraticResult = {
  socratic: boolean;
  grounded: boolean;
  answer_withheld: boolean;
  guiding_questions: string[];
  response: string;
  citations: Citation[];
};

export type AtRiskRow = {
  student_id: string;
  student_name: string;
  year_level: number;
  risk_band: string;
  score: number;
  absence_rate: number;
  avg_grade: number | null;
  major_incidents: number;
  factors: string[];
};

export type AtRiskResponse = {
  summary: { high: number; medium: number; low: number };
  students: AtRiskRow[];
};
