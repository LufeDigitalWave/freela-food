// TypeScript interfaces mapeando os schemas do backend

export interface User {
  id: string;
  email: string;
  role: "freelancer" | "establishment" | "admin";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface FreelancerProfile {
  user_id: string;
  display_name: string;
  bio: string | null;
  phone: string | null;
  avatar_url: string | null;
  service_radius_km: number | null;
  no_show_count: number;
  completed_contracts_count: number;
  average_rating: number | null;
  total_reviews: number;
  pix_key: string | null;
}

export interface JobPosting {
  id: string;
  establishment_id: string;
  skill_category_id: string;
  title: string;
  description?: string;
  start_at: string;
  end_at: string;
  hourly_rate: string | null;
  total_pay: string | null;
  status: "draft" | "open" | "filled" | "cancelled" | "completed";
  created_at: string;
  distance_m?: number;
}

export interface JobSearchResponse {
  items: JobPosting[];
  total: number;
  page: number;
  page_size: number;
}

export interface Application {
  id: string;
  job_posting_id: string;
  freelancer_id: string;
  status: "pending" | "accepted" | "rejected" | "withdrawn";
  message: string | null;
  created_at: string;
}

export interface ApplicationList {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
}

export interface ServiceContract {
  id: string;
  application_id: string | null;
  invitation_id: string | null;
  job_posting_id: string | null;
  freelancer_id: string;
  establishment_id: string;
  start_at: string;
  end_at: string;
  agreed_hourly_rate: string | null;
  agreed_total_pay: string | null;
  status: "scheduled" | "in_progress" | "completed" | "cancelled";
  cancelled_by: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  no_show: boolean;
  created_at: string;
}

export interface ContractList {
  items: ServiceContract[];
  total: number;
  page: number;
  page_size: number;
}

export interface Review {
  id: string;
  contract_id: string;
  reviewer_id: string;
  reviewee_id: string;
  stars: number;
  comment: string | null;
  visible_at: string | null;
  created_at: string;
  reviewer_display_name: string | null;
}

export interface ReviewList {
  items: Review[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReviewStats {
  average_rating: number | null;
  total_reviews: number;
  distribution: Record<number, number>;
}

export interface Payment {
  id: string;
  contract_id: string;
  amount: string;
  status: "pending" | "confirmed" | "disputed";
  pix_key: string | null;
  confirmed_at: string | null;
  confirmed_by: string | null;
  disputed_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface PaymentList {
  items: Payment[];
  total: number;
  page: number;
  page_size: number;
}

export interface FreelancerSearchRead {
  user_id: string;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  completed_contracts_count: number;
  no_show_count: number;
  distance_m: number;
  average_rating: number | null;
  total_reviews: number;
}

export interface FreelancerSearchList {
  items: FreelancerSearchRead[];
  total: number;
  page: number;
  page_size: number;
}

export interface Invitation {
  id: string;
  establishment_id: string;
  freelancer_id: string;
  skill_category_id: string;
  start_at: string;
  end_at: string;
  proposed_hourly_rate: string | null;
  proposed_total_pay: string | null;
  message: string | null;
  status: "pending" | "accepted" | "declined" | "withdrawn" | "expired";
  expires_at: string;
  decided_at: string | null;
  created_at: string;
}

export interface InvitationList {
  items: Invitation[];
  total: number;
  page: number;
  page_size: number;
}

export interface Notification {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

export interface NotificationList {
  items: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}
