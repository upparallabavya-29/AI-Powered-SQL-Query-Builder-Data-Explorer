import axios from "axios";
import type {
  UploadedSchema,
  QueryHistoryItem,
  SavedQueryItem,
  QueryResult,
  ApiResponseEnvelope
} from "../types";

// Base API URL configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000/api" : "/api");

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

// Response interceptor to extract data envelope
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Return standard error payload if available in response
    if (error.response && error.response.data) {
      return Promise.reject(error.response.data);
    }
    return Promise.reject({
      success: false,
      message: error.message || "Network communication failed.",
      errors: [error.message]
    });
  }
);

export const apiService = {
  // Schema Upload operations
  async uploadSchema(name: string, schemaType: "sql" | "json", rawContent: string): Promise<UploadedSchema> {
    const res = await apiClient.post<ApiResponseEnvelope<UploadedSchema>>("/schemas", {
      name,
      schema_type: schemaType,
      raw_content: rawContent
    });
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    throw new Error(res.data.message || "Failed to upload schema.");
  },

  async listSchemas(): Promise<UploadedSchema[]> {
    const res = await apiClient.get<ApiResponseEnvelope<UploadedSchema[]>>("/schemas");
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    return [];
  },

  async getSchema(schemaId: string): Promise<UploadedSchema> {
    const res = await apiClient.get<ApiResponseEnvelope<UploadedSchema>>(`/schemas/${schemaId}`);
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    throw new Error(res.data.message || "Failed to fetch schema details.");
  },

  // SQL Query generation & validation operations
  async generateSql(schemaId: string, prompt: string): Promise<{ query_history_id: string; generated_sql: string }> {
    const res = await apiClient.post<ApiResponseEnvelope<{ query_history_id: string; generated_sql: string }>>(
      "/queries/generate",
      { schema_id: schemaId, prompt }
    );
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    throw new Error(res.data.message || "Failed to generate SQL.");
  },

  async validateSql(sql: string): Promise<{ valid: boolean; message: string; errors: string[] }> {
    const res = await apiClient.post<ApiResponseEnvelope<{ valid: boolean; message: string; errors: string[] }>>(
      "/queries/validate",
      { sql }
    );
    if (res.data.data) {
      return res.data.data;
    }
    throw new Error(res.data.message || "Failed to validate SQL.");
  },

  async executeSql(
    schemaId: string,
    sql: string,
    limit: number,
    offset: number,
    queryHistoryId?: string
  ): Promise<QueryResult> {
    const res = await apiClient.post<ApiResponseEnvelope<QueryResult>>("/queries/execute", {
      schema_id: schemaId,
      sql,
      limit,
      offset,
      query_history_id: queryHistoryId
    });
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    throw new Error(res.data.message || "Failed to execute query.");
  },

  // Query History operations
  async listHistory(schemaId: string): Promise<QueryHistoryItem[]> {
    const res = await apiClient.get<ApiResponseEnvelope<QueryHistoryItem[]>>(`/queries/history/${schemaId}`);
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    return [];
  },

  async clearHistory(schemaId: string): Promise<void> {
    await apiClient.delete<ApiResponseEnvelope<any>>(`/queries/history/${schemaId}`);
  },

  async deleteHistoryItem(historyId: string): Promise<void> {
    await apiClient.delete<ApiResponseEnvelope<any>>(`/queries/history-item/${historyId}`);
  },

  async toggleFavorite(queryHistoryId: string): Promise<{ is_favorite: boolean }> {
    const res = await apiClient.post<ApiResponseEnvelope<{ is_favorite: boolean }>>("/queries/favorites", {
      query_history_id: queryHistoryId
    });
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    throw new Error(res.data.message || "Failed to toggle favorite status.");
  },

  async listFavorites(schemaId: string): Promise<QueryHistoryItem[]> {
    const res = await apiClient.get<ApiResponseEnvelope<QueryHistoryItem[]>>(`/queries/favorites/${schemaId}`);
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    return [];
  },

  // Saved Queries operations
  async saveQuery(schemaId: string, name: string, prompt: string | null, sqlQuery: string): Promise<SavedQueryItem> {
    const res = await apiClient.post<ApiResponseEnvelope<SavedQueryItem>>("/queries/saved", {
      schema_id: schemaId,
      name,
      prompt,
      sql_query: sqlQuery
    });
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    throw new Error(res.data.message || "Failed to save query.");
  },

  async listSavedQueries(schemaId: string): Promise<SavedQueryItem[]> {
    const res = await apiClient.get<ApiResponseEnvelope<SavedQueryItem[]>>(`/queries/saved/${schemaId}`);
    if (res.data.success && res.data.data) {
      return res.data.data;
    }
    return [];
  },

  async deleteSavedQuery(queryId: string): Promise<void> {
    await apiClient.delete<ApiResponseEnvelope<any>>(`/queries/saved/${queryId}`);
  }
};
