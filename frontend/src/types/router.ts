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
  delegate_email?: string;
  health_status?: 'online' | 'offline' | 'unknown';
  last_health_check?: string;
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

// OpenAPI Specification Types
export interface OpenAPISchema {
  type?: string;
  title?: string;
  description?: string;
  format?: string;
  enum?: string[];
  items?: OpenAPISchema;
  properties?: Record<string, OpenAPISchema>;
  required?: string[];
  anyOf?: OpenAPISchema[];
  additionalProperties?: boolean | OpenAPISchema;
  maximum?: number;
  minimum?: number;
  $ref?: string;
}

export interface OpenAPIResponse {
  description: string;
  content?: {
    'application/json': {
      schema: OpenAPISchema;
    };
  };
}

export interface OpenAPIParameter {
  name: string;
  in: string;
  required: boolean;
  schema: OpenAPISchema;
}

export interface OpenAPIRequestBody {
  content: {
    'application/json': {
      schema: OpenAPISchema;
    };
  };
  required?: boolean;
}

export interface OpenAPIOperation {
  tags: string[];
  summary: string;
  description: string;
  operationId: string;
  parameters?: OpenAPIParameter[];
  requestBody?: OpenAPIRequestBody;
  responses: Record<string, OpenAPIResponse>;
}

export interface OpenAPIPaths {
  [path: string]: {
    [method: string]: OpenAPIOperation;
  };
}

export interface OpenAPIComponents {
  schemas: Record<string, OpenAPISchema>;
}

export interface OpenAPIInfo {
  title: string;
  description: string;
  version: string;
}

export interface OpenAPISpecification {
  openapi: string;
  info: OpenAPIInfo;
  paths: OpenAPIPaths;
  components: OpenAPIComponents;
}

export interface RouterMetadataResponse {
  summary: string;
  description: string;
  tags: string[];
  code_hash: string;
  author: string;
  endpoints?: OpenAPISpecification;
}

// Legacy endpoint info for backward compatibility
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
  endpoints?: OpenAPISpecification;
}

export interface RouterList {
  routers: Router[];
}

export interface RouterServiceStatus {
  name: string;
  status: string;
  url?: string;
}

export interface RouterRunStatus {
  url?: string;
  status: string;
  services: RouterServiceStatus[];
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T & {
    isAsync?: boolean;
    message?: string;
  };
  error?: string;
  message?: string;
  statusCode?: number;
}

// Gatekeeper/Delegation Types (matching backend schemas)
export interface AvailableDelegatesResponse {
  delegates: string[];
}

export interface DelegateRouterRequest {
  router_name: string;
  delegate_email: string;
}

export interface DelegateRouterResponse {
  router: Router;
}

export interface RevokeDelegationRequest {
  router_name: string;
}

export interface RevokeDelegationResponse {
  success: boolean;
  message?: string;
}

export interface DelegateControlRequest {
  router_name: string;
  delegate_email: string;
  control_type: 'update_pricing';
  control_data: {
    pricing_updates: Array<{
      service_type: string;
      new_pricing: number;
      new_charge_type: string;
    }>;
  };
  delegate_access_token: string;
  reason?: string;
}

export interface DelegateControlResponse {
  success: boolean;
  router_name: string;
  message?: string;
}

export interface DelegateLog {
  router_name: string;
  delegate_email: string;
  control_type: string;
  control_data: Record<string, any>;
  reason?: string;
  created_at: string;
  updated_at: string;
}

export interface DCALogsResponse {
  audit_logs: DelegateLog[];
}

export interface DelegateStatus {
  is_delegate: boolean;
  delegated_routers?: string[];
} 