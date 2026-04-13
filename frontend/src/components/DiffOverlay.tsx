import React from 'react';
import { DiffItem, DiffType } from '../services/types';

interface DiffOverlayProps {
  diffItems: DiffItem[];
  /** The page number this overlay is scoped to */
  pageNumber: number;
  /** Actual rendered width of the PDF canvas (px) */
  renderedWidth: number;
  /** Actual rendered height of the PDF canvas (px) */
  renderedHeight: number;
  /** Original PDF page width in PDF points (usually 595 for A4) */
  pdfPageWidth: number;
  /** Original PDF page height in PDF points (usually 842 for A4) */
  pdfPageHeight: number;
  selectedDiffId?: string | null;
  onDiffClick?: (diff: DiffItem) => void;
}

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

const DiffOverlay: React.FC<DiffOverlayProps> = ({
  diffItems,
  pageNumber,
  renderedWidth,
  renderedHeight,
  pdfPageWidth,
  pdfPageHeight,
  selectedDiffId = null,
  onDiffClick,
}) => {
  // Filter diffs for this specific page
  const pageDiffs = diffItems.filter((diff) => {
    const bbox = diff.new_bbox || diff.old_bbox;
    return bbox && bbox.page === pageNumber;
  });

  if (pageDiffs.length === 0) {
    return null;
  }

  const scaleX = renderedWidth / pdfPageWidth;
  const scaleY = renderedHeight / pdfPageHeight;

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ width: renderedWidth, height: renderedHeight }}>
      {pageDiffs.map((diff) => {
        const bbox = diff.new_bbox || diff.old_bbox;
        if (!bbox) return null;

        const x = bbox.x0 * scaleX;
        const y = (pdfPageHeight - bbox.y1) * scaleY; // PDF Y axis is bottom-up
        const width = (bbox.x1 - bbox.x0) * scaleX;
        const height = (bbox.y1 - bbox.y0) * scaleY;

        const colorClass = getDiffColor(diff.diff_type);
        const label = getDiffLabel(diff.diff_type);
        const isSelected = selectedDiffId === diff.id;

        return (
          <div
            key={diff.id}
            className={`${colorClass} cursor-pointer group pointer-events-auto ${isSelected ? 'is-selected' : ''}`}
            style={{
              position: 'absolute',
              left: `${x}px`,
              top: `${y}px`,
              width: `${Math.max(width, 4)}px`,
              height: `${Math.max(height, 4)}px`,
            }}
            onClick={() => onDiffClick?.(diff)}
            title={`${label}: ${diff.old_value || ''} → ${diff.new_value || ''}`}
          >
            {/* Tooltip on hover */}
            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
              <div className="bg-gray-900 text-white text-xs py-1 px-2 rounded whitespace-nowrap max-w-[200px] truncate">
                {label}
              </div>
              <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900" />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DiffOverlay;
