export type Campaign = {
  id: number;
  title: string;
  description: string;
  deadline: string | null;
  image_formats: string;
  max_image_mb: number;
  link_token: string;
};

export type CheckReport = {
  missing: string[];
  format_issues: string[];
  notes: string;
};

export type SubmissionResult = {
  applicant_id: number;
  status: string;
  report: CheckReport;
};

export type WorkRow = {
  work_id: number;
  title: string;
  dimensions: string;
  medium: string;
  school: string;
  price: string;
  image_path: string;
  resume_path: string;
  applicant_id: number;
  applicant_name: string;
  applicant_phone: string;
  applicant_email: string;
  applicant_wechat: string;
};

export type Artist = {
  name: string;
  phone: string;
  email: string;
  wechat: string;
  work_count: number;
  status: string;
  resume_path: string;
};

export type Overview = {
  campaign_id: number;
  campaign_title: string;
  applicant_count: number;
  work_count: number;
  school_distribution: Record<string, number>;
  medium_distribution: Record<string, number>;
  artist_list: Artist[];
};

export type BriefResult = {
  overview: Overview;
  brief: string;
  source: "llm" | "deterministic";
};

export type QueryResult = {
  answer: string;
  tool: string | null;
  used_llm: boolean;
};
