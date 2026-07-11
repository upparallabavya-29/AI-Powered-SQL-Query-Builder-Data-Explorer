import React, { useState } from "react";
import {
  Box,
  Typography,
  Tabs,
  Tab,
  IconButton,
  List,
  ListItem,
  Card,
  CardContent,
  Tooltip,
  Button
} from "@mui/material";
import HistoryIcon from "@mui/icons-material/History";
import SaveIcon from "@mui/icons-material/Bookmark";
import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import RunIcon from "@mui/icons-material/PlayArrow";
import DeleteIcon from "@mui/icons-material/Delete";
import ClearIcon from "@mui/icons-material/DeleteSweep";
import { useAppStore } from "../store/useAppStore";
import type { QueryHistoryItem, SavedQueryItem } from "../types";

export const QueryHistorySidebar: React.FC = () => {
  const {
    history,
    savedQueries,
    setPrompt,
    setGeneratedSql,
    setQueryHistoryId,
    executeSql,
    toggleFavorite,
    deleteHistoryItem,
    clearHistory,
    deleteSavedQuery
  } = useAppStore();

  const [activeTab, setActiveTab] = useState<number>(0);

  const handleTabChange = (_: any, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleReRunHistory = (item: QueryHistoryItem) => {
    setPrompt(item.prompt);
    setGeneratedSql(item.generated_sql);
    setQueryHistoryId(item.id);
    executeSql(item.generated_sql, 100, 0);
  };

  const handleReRunSaved = (item: SavedQueryItem) => {
    if (item.prompt) setPrompt(item.prompt);
    setGeneratedSql(item.sql_query);
    setQueryHistoryId(null); // Fresh run for saved templates
    executeSql(item.sql_query, 100, 0);
  };

  const formatTime = (ms: number | null) => {
    if (ms === null || ms === undefined) return "N/A";
    return `${ms}ms`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <Box
      className="glass-panel"
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        p: 2,
        overflow: "hidden"
      }}
    >
      {/* Tabs Selector */}
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        variant="fullWidth"
        sx={{
          mb: 2,
          minHeight: "unset",
          "& .MuiTab-root": {
            py: 1,
            minHeight: "unset",
            fontWeight: 700,
            fontSize: "13px"
          }
        }}
      >
        <Tab icon={<HistoryIcon sx={{ fontSize: 18 }} />} label="History" />
        <Tab icon={<SaveIcon sx={{ fontSize: 18 }} />} label="Saved" />
      </Tabs>

      {/* History panel */}
      {activeTab === 0 && (
        <Box sx={{ display: "flex", flexDirection: "column", flexGrow: 1, overflow: "hidden" }}>
          {history.length > 0 && (
            <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
              <Button
                size="small"
                color="error"
                startIcon={<ClearIcon />}
                onClick={clearHistory}
                sx={{ fontSize: "11px", py: 0.25, borderRadius: "6px" }}
              >
                Clear All
              </Button>
            </Box>
          )}

          <Box sx={{ flexGrow: 1, overflowY: "auto", pr: 0.5 }}>
            {history.length > 0 ? (
              <List sx={{ display: "flex", flexDirection: "column", gap: 1.5, p: 0 }}>
                {history.map((item) => (
                  <ListItem key={item.id} disablePadding>
                    <Card sx={{ width: "100%", borderRadius: "8px" }}>
                      <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                        {/* Prompt Question */}
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, lineBreak: "anywhere" }}>
                          "{item.prompt}"
                        </Typography>

                        {/* SQL Preview */}
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{
                            display: "block",
                            fontFamily: "var(--font-mono)",
                            backgroundColor: "rgba(0,0,0,0.2)",
                            p: 1,
                            borderRadius: "4px",
                            mb: 1,
                            whiteSpace: "pre-wrap",
                            fontSize: "10px",
                            lineBreak: "anywhere"
                          }}
                        >
                          {item.generated_sql}
                        </Typography>

                        {/* Metadata row */}
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <Box sx={{ display: "flex", flexDirection: "column" }}>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: "9px" }}>
                              {formatDate(item.created_at)}
                            </Typography>
                            <Typography variant="caption" sx={{ fontSize: "9px", fontWeight: 600, color: "var(--primary)" }}>
                              Exec: {formatTime(item.execution_time_ms)}
                            </Typography>
                          </Box>

                          <Box sx={{ display: "flex", gap: 0.25 }}>
                            <Tooltip title={item.is_favorite ? "Remove from Favorites" : "Add to Favorites"}>
                              <IconButton size="small" onClick={() => toggleFavorite(item.id)}>
                                {item.is_favorite ? (
                                  <StarIcon sx={{ fontSize: 16, color: "var(--warning)" }} />
                                ) : (
                                  <StarBorderIcon sx={{ fontSize: 16 }} />
                                )}
                              </IconButton>
                            </Tooltip>
                            
                            <Tooltip title="Re-run Query">
                              <IconButton size="small" color="primary" onClick={() => handleReRunHistory(item)}>
                                <RunIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>

                            <Tooltip title="Delete">
                              <IconButton size="small" color="error" onClick={() => deleteHistoryItem(item.id)}>
                                <DeleteIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ textAlign: "center", mt: 6, px: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  No query history logs found.
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      )}

      {/* Saved queries panel */}
      {activeTab === 1 && (
        <Box sx={{ display: "flex", flexDirection: "column", flexGrow: 1, overflow: "hidden" }}>
          <Box sx={{ flexGrow: 1, overflowY: "auto", pr: 0.5 }}>
            {savedQueries.length > 0 ? (
              <List sx={{ display: "flex", flexDirection: "column", gap: 1.5, p: 0 }}>
                {savedQueries.map((item) => (
                  <ListItem key={item.id} disablePadding>
                    <Card sx={{ width: "100%", borderRadius: "8px" }}>
                      <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                        {/* Name */}
                        <Typography variant="body2" sx={{ fontWeight: 700, color: "var(--primary)", mb: 0.5 }}>
                          {item.name}
                        </Typography>

                        {/* Prompt if available */}
                        {item.prompt && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1, fontStyle: "italic" }}>
                            "{item.prompt}"
                          </Typography>
                        )}

                        {/* SQL Preview */}
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{
                            display: "block",
                            fontFamily: "var(--font-mono)",
                            backgroundColor: "rgba(0,0,0,0.2)",
                            p: 1,
                            borderRadius: "4px",
                            mb: 1.5,
                            whiteSpace: "pre-wrap",
                            fontSize: "10px",
                            lineBreak: "anywhere"
                          }}
                        >
                          {item.sql_query}
                        </Typography>

                        {/* Actions */}
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: "9px" }}>
                            {formatDate(item.created_at)}
                          </Typography>

                          <Box sx={{ display: "flex", gap: 0.5 }}>
                            <Tooltip title="Run Query">
                              <IconButton size="small" color="primary" onClick={() => handleReRunSaved(item)}>
                                <RunIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>
                            
                            <Tooltip title="Delete Saved Query">
                              <IconButton size="small" color="error" onClick={() => deleteSavedQuery(item.id)}>
                                <DeleteIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ textAlign: "center", mt: 6, px: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  No saved queries found.
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      )}
    </Box>
  );
};
export default QueryHistorySidebar;
