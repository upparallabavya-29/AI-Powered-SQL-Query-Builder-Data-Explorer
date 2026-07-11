export interface SchemaColumn {
  name: string;
  type: string;
}

export interface UploadedSchema {
  id: string;
  name: string;
  schema_type: "sql" | "json";
  parsed_tables: Record<string, SchemaColumn[]>;
  created_at: string;
}

export interface QueryHistoryItem {
  id: string;
  schema_id: string;
  prompt: string;
  generated_sql: string;
  execution_time_ms: number | null;
  created_at: string;
  is_favorite: boolean;
}

export interface SavedQueryItem {
  id: string;
  schema_id: string;
  name: string;
  prompt: string | null;
  sql_query: string;
  created_at: string;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, any>[];
  execution_time_ms: number;
  total_rows: number;
  has_more: boolean;
}

export interface ApiResponseEnvelope<T> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
}
