import { create } from "zustand";
import type {
  UploadedSchema,
  QueryHistoryItem,
  SavedQueryItem,
  QueryResult
} from "../types";
import { apiService } from "../services/api";

interface LoadingStates {
  generating: boolean;
  executing: boolean;
  validating: boolean;
  schemas: boolean;
}

interface ErrorStates {
  sql: string[];
  general: string;
}

interface AppState {
  schemas: UploadedSchema[];
  selectedSchemaId: string | null;
  prompt: string;
  generatedSql: string;
  queryHistoryId: string | null;
  queryResult: QueryResult | null;
  history: QueryHistoryItem[];
  savedQueries: SavedQueryItem[];
  favorites: QueryHistoryItem[];
  loadingStates: LoadingStates;
  errors: ErrorStates;
  
  // Setters
  setSchemas: (schemas: UploadedSchema[]) => void;
  selectSchemaId: (schemaId: string | null) => void;
  setPrompt: (prompt: string) => void;
  setGeneratedSql: (sql: string) => void;
  setQueryHistoryId: (historyId: string | null) => void;
  setQueryResult: (result: QueryResult | null) => void;
  setHistory: (history: QueryHistoryItem[]) => void;
  setSavedQueries: (queries: SavedQueryItem[]) => void;
  setFavorites: (favorites: QueryHistoryItem[]) => void;
  clearSqlErrors: () => void;
  clearGeneralError: () => void;

  // Actions
  fetchSchemas: () => Promise<void>;
  loadSchemaContext: (schemaId: string) => Promise<void>;
  generateSql: (prompt: string) => Promise<string>;
  validateSql: (sql: string) => Promise<boolean>;
  executeSql: (sql: string, limit?: number, offset?: number) => Promise<void>;
  saveQuery: (name: string) => Promise<void>;
  deleteSavedQuery: (queryId: string) => Promise<void>;
  toggleFavorite: (historyId: string) => Promise<void>;
  clearHistory: () => Promise<void>;
  deleteHistoryItem: (historyId: string) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  schemas: [],
  selectedSchemaId: null,
  prompt: "",
  generatedSql: "",
  queryHistoryId: null,
  queryResult: null,
  history: [],
  savedQueries: [],
  favorites: [],
  loadingStates: {
    generating: false,
    executing: false,
    validating: false,
    schemas: false
  },
  errors: {
    sql: [],
    general: ""
  },

  // Setters
  setSchemas: (schemas) => set({ schemas }),
  selectSchemaId: (schemaId) => {
    set({
      selectedSchemaId: schemaId,
      prompt: "",
      generatedSql: "",
      queryHistoryId: null,
      queryResult: null,
      errors: { sql: [], general: "" }
    });
    if (schemaId) {
      get().loadSchemaContext(schemaId);
    }
  },
  setPrompt: (prompt) => set({ prompt }),
  setGeneratedSql: (generatedSql) => set({ generatedSql }),
  setQueryHistoryId: (queryHistoryId) => set({ queryHistoryId }),
  setQueryResult: (queryResult) => set({ queryResult }),
  setHistory: (history) => set({ history }),
  setSavedQueries: (savedQueries) => set({ savedQueries }),
  setFavorites: (favorites) => set({ favorites }),
  clearSqlErrors: () => set((state) => ({ errors: { ...state.errors, sql: [] } })),
  clearGeneralError: () => set((state) => ({ errors: { ...state.errors, general: "" } })),

  // Actions
  fetchSchemas: async () => {
    set((state) => ({ loadingStates: { ...state.loadingStates, schemas: true } }));
    try {
      const schemas = await apiService.listSchemas();
      set({ schemas });
      // Auto-select first schema if nothing selected and schemas are present
      if (schemas.length > 0 && !get().selectedSchemaId) {
        get().selectSchemaId(schemas[0].id);
      }
    } catch (e: any) {
      set((state) => ({ errors: { ...state.errors, general: e.message || "Failed to fetch database schemas." } }));
    } finally {
      set((state) => ({ loadingStates: { ...state.loadingStates, schemas: false } }));
    }
  },

  loadSchemaContext: async (schemaId) => {
    try {
      const [history, saved, favorites] = await Promise.all([
        apiService.listHistory(schemaId),
        apiService.listSavedQueries(schemaId),
        apiService.listFavorites(schemaId)
      ]);
      set({ history, savedQueries: saved, favorites });
    } catch (e: any) {
      console.error("Failed to load schema context items", e);
    }
  },

  generateSql: async (promptText) => {
    const schemaId = get().selectedSchemaId;
    if (!schemaId) throw new Error("No database schema selected.");
    
    set((state) => ({
      loadingStates: { ...state.loadingStates, generating: true },
      errors: { ...state.errors, sql: [] }
    }));
    
    try {
      const data = await apiService.generateSql(schemaId, promptText);
      set({
        generatedSql: data.generated_sql,
        queryHistoryId: data.query_history_id
      });
      // Refresh history sidebar list
      const updatedHistory = await apiService.listHistory(schemaId);
      set({ history: updatedHistory });
      return data.generated_sql;
    } catch (e: any) {
      const errMsg = e.message || "Failed to generate SQL from your prompt.";
      set((state) => ({ errors: { ...state.errors, sql: [errMsg] } }));
      throw e;
    } finally {
      set((state) => ({ loadingStates: { ...state.loadingStates, generating: false } }));
    }
  },

  validateSql: async (sqlText) => {
    set((state) => ({
      loadingStates: { ...state.loadingStates, validating: true },
      errors: { ...state.errors, sql: [] }
    }));
    try {
      const res = await apiService.validateSql(sqlText);
      if (!res.valid) {
        set((state) => ({ errors: { ...state.errors, sql: res.errors } }));
      }
      return res.valid;
    } catch (e: any) {
      const errMsg = e.message || "Failed to validate SQL statement.";
      set((state) => ({ errors: { ...state.errors, sql: [errMsg] } }));
      return false;
    } finally {
      set((state) => ({ loadingStates: { ...state.loadingStates, validating: false } }));
    }
  },

  executeSql: async (sqlText, limit = 100, offset = 0) => {
    const schemaId = get().selectedSchemaId;
    if (!schemaId) throw new Error("No database schema selected.");

    set((state) => ({
      loadingStates: { ...state.loadingStates, executing: true },
      errors: { ...state.errors, sql: [] }
    }));

    try {
      const historyId = get().queryHistoryId || undefined;
      const result = await apiService.executeSql(schemaId, sqlText, limit, offset, historyId);
      set({ queryResult: result });
      
      // Reload history to reflect the updated execution times
      const updatedHistory = await apiService.listHistory(schemaId);
      set({ history: updatedHistory });
    } catch (e: any) {
      const errMsgs = e.errors || [e.message || "Failed to execute SQL query."];
      set((state) => ({ errors: { ...state.errors, sql: errMsgs }, queryResult: null }));
    } finally {
      set((state) => ({ loadingStates: { ...state.loadingStates, executing: false } }));
    }
  },

  saveQuery: async (name) => {
    const schemaId = get().selectedSchemaId;
    const sql = get().generatedSql;
    const prompt = get().prompt;
    if (!schemaId || !sql) throw new Error("Need an active schema and generated SQL query to save.");

    try {
      await apiService.saveQuery(schemaId, name, prompt || null, sql);
      const saved = await apiService.listSavedQueries(schemaId);
      set({ savedQueries: saved });
    } catch (e: any) {
      set((state) => ({ errors: { ...state.errors, general: e.message || "Failed to save query." } }));
      throw e;
    }
  },

  deleteSavedQuery: async (queryId) => {
    const schemaId = get().selectedSchemaId;
    if (!schemaId) return;
    try {
      await apiService.deleteSavedQuery(queryId);
      const saved = await apiService.listSavedQueries(schemaId);
      set({ savedQueries: saved });
    } catch (e: any) {
      set((state) => ({ errors: { ...state.errors, general: e.message || "Failed to delete saved query." } }));
    }
  },

  toggleFavorite: async (historyId) => {
    const schemaId = get().selectedSchemaId;
    if (!schemaId) return;
    try {
      await apiService.toggleFavorite(historyId);
      // Reload history and favorites
      const [history, favorites] = await Promise.all([
        apiService.listHistory(schemaId),
        apiService.listFavorites(schemaId)
      ]);
      set({ history, favorites });
    } catch (e: any) {
      console.error("Failed to toggle favorite", e);
    }
  },

  clearHistory: async () => {
    const schemaId = get().selectedSchemaId;
    if (!schemaId) return;
    try {
      await apiService.clearHistory(schemaId);
      set({ history: [], favorites: [] });
    } catch (e: any) {
      console.error("Failed to clear query history", e);
    }
  },

  deleteHistoryItem: async (historyId) => {
    const schemaId = get().selectedSchemaId;
    if (!schemaId) return;
    try {
      await apiService.deleteHistoryItem(historyId);
      const [history, favorites] = await Promise.all([
        apiService.listHistory(schemaId),
        apiService.listFavorites(schemaId)
      ]);
      set({ history, favorites });
    } catch (e: any) {
      console.error("Failed to delete history item", e);
    }
  }
}));
