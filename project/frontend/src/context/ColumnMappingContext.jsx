import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const ColumnMappingContext = createContext({
  mappingInfo: {},
  tableColumns: {},
  resolveColumn: (fileOrTable, internalCol) => internalCol,
  resolveColumns: (fileOrTable, internalCols) => internalCols,
  formatDynamicText: (text) => text,
  renderDynamicText: (text) => text,
  refreshMapping: () => {},
});

/**
 * Normalizes file string (e.g. 'sales.csv' -> 'sales', 'sales' -> 'sales')
 */
export function normalizeTableKey(fileOrTable) {
  if (!fileOrTable) return '';
  const s = String(fileOrTable).toLowerCase().trim();
  return s.replace(/\.csv$/, '');
}

/**
 * Standalone column resolver helper
 */
export function resolveColumnStandalone(mappingInfo, fileOrTable, internalCol) {
  if (!internalCol) return '';
  const table = normalizeTableKey(fileOrTable);
  const userMapped = mappingInfo?.[table]?.mapping?.[internalCol];
  if (userMapped && typeof userMapped === 'string' && userMapped.trim().length > 0) {
    return userMapped.trim();
  }
  return internalCol;
}

export function ColumnMappingProvider({ children }) {
  const [mappingInfo, setMappingInfo] = useState({});
  const [tableColumns, setTableColumns] = useState({});

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.getUploadStatus();
      if (res) {
        if (res.mapping_info) setMappingInfo(res.mapping_info);
        if (res.table_columns) setTableColumns(res.table_columns);
      }
    } catch {
      // Keep defaults gracefully if server is initializing
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const resolveColumn = useCallback(
    (fileOrTable, internalCol) => {
      return resolveColumnStandalone(mappingInfo, fileOrTable, internalCol);
    },
    [mappingInfo]
  );

  const resolveColumns = useCallback(
    (fileOrTable, internalCols) => {
      if (!internalCols) return [];
      const cols = Array.isArray(internalCols) ? internalCols : [internalCols];
      return cols.map((col) => resolveColumn(fileOrTable, col));
    },
    [resolveColumn]
  );

  /**
   * Replaces placeholders like {sales:total_price} or {products:cost} or {total_price}
   * with the actual resolved column name string.
   */
  const formatDynamicText = useCallback(
    (text, defaultTable = 'sales') => {
      if (!text || typeof text !== 'string') return text;
      return text.replace(/\{([a-zA-Z0-9_\-.]+)(?::([a-zA-Z0-9_]+))?\}/g, (match, p1, p2) => {
        let table = defaultTable;
        let col = p1;
        if (p2) {
          table = p1;
          col = p2;
        }
        return resolveColumn(table, col);
      });
    },
    [resolveColumn]
  );

  /**
   * Parses text with placeholders and returns React elements with styled badges for columns.
   */
  const renderDynamicText = useCallback(
    (text, defaultTable = 'sales') => {
      if (!text || typeof text !== 'string') return text;
      const regex = /\{([a-zA-Z0-9_\-.]+)(?::([a-zA-Z0-9_]+))?\}/g;
      const parts = [];
      let lastIndex = 0;
      let match;

      while ((match = regex.exec(text)) !== null) {
        if (match.index > lastIndex) {
          parts.push(text.substring(lastIndex, match.index));
        }
        let table = defaultTable;
        let col = match[1];
        if (match[2]) {
          table = match[1];
          col = match[2];
        }
        const resolved = resolveColumn(table, col);
        parts.push(
          <code key={`${match.index}-${col}`} className="source-dyn-col-chip" title={`Mapped from internal field: ${col}`}>
            {resolved}
          </code>
        );
        lastIndex = regex.lastIndex;
      }

      if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex));
      }

      return parts;
    },
    [resolveColumn]
  );

  return (
    <ColumnMappingContext.Provider
      value={{
        mappingInfo,
        tableColumns,
        resolveColumn,
        resolveColumns,
        formatDynamicText,
        renderDynamicText,
        refreshMapping: fetchStatus,
      }}
    >
      {children}
    </ColumnMappingContext.Provider>
  );
}

export function useColumnMapping() {
  return useContext(ColumnMappingContext);
}

export default ColumnMappingContext;
