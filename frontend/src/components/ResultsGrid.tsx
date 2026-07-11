import React, { useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender
} from "@tanstack/react-table";
import type { ColumnDef, SortingState } from "@tanstack/react-table";
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  TablePagination,
  CircularProgress,
  Divider
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import DbIcon from "@mui/icons-material/Storage";
import EmptyIcon from "@mui/icons-material/HelpOutlined";
import { useAppStore } from "../store/useAppStore";

export const ResultsGrid: React.FC = () => {
  const { queryResult, loadingStates, errors } = useAppStore();
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(10);

  // Parse columns & rows from Zustand state
  const tableData = useMemo(() => queryResult?.rows || [], [queryResult]);
  const tableColumns = useMemo(() => queryResult?.columns || [], [queryResult]);

  // Construct TanStack columns schema dynamically
  const columns = useMemo<ColumnDef<Record<string, any>>[]>(() => {
    return tableColumns.map((colName) => ({
      accessorKey: colName,
      header: colName,
      cell: (info) => {
        const val = info.getValue();
        if (val === null || val === undefined) {
          return <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>NULL</span>;
        }
        return String(val);
      }
    }));
  }, [tableColumns]);

  // Initialize TanStack Table Hook
  const table = useReactTable({
    data: tableData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    debugTable: false
  });

  // Handle Material UI Pagination sync
  React.useEffect(() => {
    table.setPageSize(rowsPerPage);
    table.setPageIndex(page);
  }, [page, rowsPerPage, table]);

  // CSV Export implementation
  const handleCsvExport = () => {
    if (tableData.length === 0) return;
    
    // Construct header row
    const headers = tableColumns.join(",");
    
    // Format records escaping commas and double-quotes
    const bodyRows = tableData.map((row) =>
      tableColumns
        .map((col) => {
          const val = row[col];
          if (val === null || val === undefined) return "";
          const strVal = String(val).replace(/"/g, '""');
          return strVal.includes(",") || strVal.includes("\n") || strVal.includes('"')
            ? `"${strVal}"`
            : strVal;
        })
        .join(",")
    );

    const csvContent = [headers, ...bodyRows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `athena_query_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleChangePage = (_: any, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (loadingStates.executing) {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 280, gap: 2 }}>
        <CircularProgress color="primary" />
        <Typography variant="body2" color="text.secondary">
          Running query against sandbox database...
        </Typography>
      </Box>
    );
  }

  if (errors.sql.length > 0) {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 280, p: 3, border: "1px dashed rgba(239, 68, 68, 0.2)", borderRadius: 2 }}>
        <EmptyIcon sx={{ fontSize: 40, color: "var(--error)", mb: 1 }} />
        <Typography variant="body1" sx={{ fontWeight: 700, color: "var(--error)" }}>
          Execution Prevented
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", mt: 0.5 }}>
          Please correct the errors in the editor before running.
        </Typography>
      </Box>
    );
  }

  if (!queryResult) {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 280, p: 3, border: "1px dashed var(--border-color)", borderRadius: 2 }}>
        <DbIcon sx={{ fontSize: 40, color: "var(--text-muted)", mb: 1 }} />
        <Typography variant="body1" sx={{ fontWeight: 600, color: "var(--text-muted)" }}>
          No Query Executed
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", mt: 0.5 }}>
          Write a natural language prompt, generate SQL, and click execute to fetch records.
        </Typography>
      </Box>
    );
  }

  if (tableData.length === 0) {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 280, p: 3, border: "1px dashed var(--border-color)", borderRadius: 2 }}>
        <EmptyIcon sx={{ fontSize: 40, color: "var(--text-muted)", mb: 1 }} />
        <Typography variant="body1" sx={{ fontWeight: 600, color: "var(--text-muted)" }}>
          Empty Result Set
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center", mt: 0.5 }}>
          The query compiled and executed successfully, but returned 0 database records.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
      {/* Grid Metadata and Export */}
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <Typography variant="body2" sx={{ fontWeight: 700, color: "var(--success)" }}>
            Success
          </Typography>
          <Divider orientation="vertical" flexItem sx={{ height: 14, my: "auto" }} />
          <Typography variant="caption" color="text.secondary">
            Returned {queryResult.total_rows} rows in{" "}
            <span style={{ fontWeight: 600, color: "var(--text-main)" }}>
              {queryResult.execution_time_ms}ms
            </span>
          </Typography>
          {queryResult.has_more && (
            <Typography variant="caption" sx={{ color: "var(--warning)", fontWeight: 500 }}>
              (Truncated to limit)
            </Typography>
          )}
        </Box>

        <Button
          size="small"
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleCsvExport}
          sx={{ borderRadius: "6px" }}
        >
          Export CSV
        </Button>
      </Box>

      {/* TanStack Data Table */}
      <TableContainer component={Paper} sx={{ maxHeight: 400, border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", overflow: "auto" }}>
        <Table stickyHeader size="small">
          <TableHead>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableCell
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    sx={{
                      cursor: header.column.getCanSort() ? "pointer" : "default",
                      userSelect: "none",
                      fontWeight: 700,
                      backgroundColor: "rgba(255, 255, 255, 0.04)",
                      fontSize: "12px",
                      py: 1,
                      borderBottom: "2px solid rgba(255,255,255,0.12)"
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === "asc" && " ▴"}
                      {header.column.getIsSorted() === "desc" && " ▾"}
                    </Box>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableHead>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id} hover sx={{ "&:hover": { backgroundColor: "rgba(255,255,255,0.02)" } }}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell
                    key={cell.id}
                    sx={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "11px",
                      py: 0.75,
                      borderBottom: "1px solid rgba(255,255,255,0.04)"
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination Controls */}
      <TablePagination
        component="div"
        count={tableData.length}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[10, 25, 50, 100]}
        sx={{
          borderTop: "none",
          "& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows": {
            fontSize: "11px"
          }
        }}
      />
    </Box>
  );
};
export default ResultsGrid;
