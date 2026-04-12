import React from 'react';
import { DiffItem, DiffType } from '../services/types';

interface DiffOverlayProps {
  diffItems: DiffItem[];
  currentPage: number;
  canvasWidth: number;
  pageWidth: number;
  pageHeight: number;
  onDiffClick?: (diff: DiffItem) => void;
  className?: string;
}

const DiffOverlay: React.FC<DiffOverlayProps> = ({
  diffItems,
  currentPage,
  canvasWidth,
  pageWidth,
  pageHeight,
  onDiffClick,
  className = '',
}) => {
  // Convert PDF bbox to screen coordinates
  const toScreenCoords = (bbox: { x0: number; y0: number; x1: number; y1: number; page: number }) => {
    if (bbox.page !== currentPage) return null;
    
    const scale = canvasWidth / pageWidth;
    const x = bbox.x0 * scale;
    const y = (pageHeight - bbox.y1) * scale; // PDF Y axis is bottom-up
    const width = (bbox.x1 - bbox.x0) * scale;
    const height = (bbox.y1 - bbox.y0) * scale;
    
    return { x, y, width, height };
  };

  const getDiffColor = (type: DiffType) => {
    switch (type) {
      case DiffType.ADDED:
        return 'diff-overlay-added';
      case DiffType.DELETED:
        return 'diff-overlay-deleted';
      case DiffType.NUMBER_MODIFIED:
        return 'diff-overlay-modified';
      case DiffType.TEXT_MODIFIED:
        return 'diff-overlay-text';
      default:
        return 'diff-overlay-text';
    }
  };

  const getDiffLabel = (type: DiffType) => {
    switch (type) {
      case DiffType.ADDED:
        return '新增';
      case DiffType.DELETED:
        return '刪除';
      case DiffType.NUMBER_MODIFIED:
        return '數值修改';
      case DiffType.TEXT_MODIFIED:
        return '文字修改';
      default:
        return '修改';
    }
  };

  // Filter diffs for current page
  const pageDiffs = diffItems.filter(diff => {
    const bbox = diff.new_bbox || diff.old_bbox;
    return bbox && bbox.page === currentPage;
  });

  if (pageDiffs.length === 0) {
    return null;
  }

  return (
    <div className={`absolute inset-0 ${className}`}>
      {pageDiffs.map((diff) => {
        const bbox = diff.new_bbox || diff.old_bbox;
        if (!bbox) return null;
        
        const coords = toScreenCoords(bbox);
        if (!coords) return null;
        
        const colorClass = getDiffColor(diff.diff_type);
        const label = getDiffLabel(diff.diff_type);
        
        return (
          <div
            key={diff.id}
            className={`${colorClass} cursor-pointer group`}
            style={{
              left: `${coords.x}px`,
              top: `${coords.y}px`,
              width: `${coords.width}px`,
              height: `${coords.height}px`,
            }}
            onClick={() => onDiffClick?.(diff)}
            title={`${label}: ${diff.old_value || ''} → ${diff.new_value || ''}`}
          >
            {/* Tooltip on hover */}
            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <div className="bg-gray-900 text-white text-xs py-1 px-2 rounded whitespace-nowrap">
                {label}
              </div>
              <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900" />
            </div>
            
            {/* Inner indicator */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-white opacity-80" />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DiffOverlay;
