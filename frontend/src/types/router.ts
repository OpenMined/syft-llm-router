export enum RouterType {
  DEFAULT = "default",
  CUSTOM = "custom"
}

export enum RouterServiceType {
  CHAT = "chat",
  SEARCH = "search"
}

export enum PricingChargeType {
  PER_REQUEST = "per_request"
}

export interface ServiceOverview {
  type: RouterServiceType;
  pricing: number;
  charge_type: PricingChargeType;
  enabled: boolean;
}

export interface Router {
  name: string;
  published: boolean;
  summary: string;
  author: string;
  services: ServiceOverview[];
}

export interface CreateRouterRequest {
  name: string;
  router_type: RouterType;
  services: RouterServiceType[];
}

export interface CreateRouterResponse {
  router_name: string;
  output_dir: string;
  router_type: RouterType;
}

export interface PublishRouterRequest {
  router_name: string;
  summary: string;
  description: string;
  tags: string[];
  services: ServiceOverview[];
}

export interface RouterMetadataResponse {
  summary: string;
  description: string;
  tags: string[];
  code_hash: string;
  author: string;
  endpoints?: Record<string, any>;
}

export interface EndpointInfo {
  path: string;
  method: string;
  description: string;
  parameters?: Record<string, string>;
  response?: string;
}

export interface RouterDetails {
  name: string;
  published: boolean;
  services?: ServiceOverview[];
  metadata?: RouterMetadataResponse;
  endpoints?: Record<string, EndpointInfo>;
}

export interface RouterList {
  routers: Router[];
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
} 