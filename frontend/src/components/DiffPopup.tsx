import React, { useState } from 'react';
import { CheckCircle, Copy, ExternalLink, Flag, X } from 'lucide-react';

import { DiffItem, DiffType } from '../services/types';

interface DiffPopupProps {
  diff: DiffItem | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (diffId: string, reviewer?: string, note?: string) => void;
  onFlag: (diffId: string, reviewer?: string, note?: string) => void;
  className?: string;
}

interface DiffPopupInnerProps extends DiffPopupProps {
  diff: DiffItem;
}

const getDiffLabel = (type: DiffType) => {
  switch (type) {
    case DiffType.ADDED:
      return '新增內容';
    case DiffType.DELETED:
      return '刪除內容';
    case DiffType.NUMBER_MODIFIED:
      return '數值修改';
    case DiffType.TEXT_MODIFIED:
      return '文字修改';
    default:
      return '內容修改';
  }
};

const getDiffColor = (type: DiffType) => {
  switch (type) {
    case DiffType.ADDED:
      return 'text-diff-added bg-diff-added/10 border-diff-added';
    case DiffType.DELETED:
      return 'text-diff-deleted bg-diff-deleted/10 border-diff-deleted';
    case DiffType.NUMBER_MODIFIED:
      return 'text-diff-modified bg-diff-modified/10 border-diff-modified';
    case DiffType.TEXT_MODIFIED:
      return 'text-diff-text bg-diff-text/10 border-diff-text';
    default:
      return 'text-gray-600 bg-gray-100 border-gray-300';
  }
};

const getCommonPrefixLength = (a: string, b: string) => {
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  return i;
};

const getCommonSuffixLength = (a: string, b: string, prefixLen: number) => {
  let i = 0;
  while (i + prefixLen < a.length && i + prefixLen < b.length && a[a.length - 1 - i] === b[b.length - 1 - i]) i++;
  return i;
};

const getTrimmedDiffText = (oldValue: string, newValue: string) => {
  const prefixLen = getCommonPrefixLength(oldValue, newValue);
  const suffixLen = getCommonSuffixLength(oldValue, newValue, prefixLen);
  const trimText = (value: string) => {
    if (prefixLen + suffixLen >= value.length) return value.trim();
    return value.slice(prefixLen, value.length - suffixLen).trim();
  };
  const oldSnippet = trimText(oldValue);
  const newSnippet = trimText(newValue);
  if (!oldSnippet && !newSnippet) {
    return `${oldValue} → ${newValue}`;
  }
  return `${oldSnippet || '[刪除]'} → ${newSnippet || '[新增]'}`;
};

const DiffPopupInner: React.FC<DiffPopupInnerProps> = ({
  diff,
  onClose,
  onConfirm,
  onFlag,
  className = '',
}) => {
  const [reviewer, setReviewer] = useState(diff.reviewed_by || '');
  const [note, setNote] = useState('');

  const handleConfirm = () => {
    onConfirm(diff.id, reviewer || undefined, note || undefined);
    onClose();
  };

  const handleFlag = () => {
    onFlag(diff.id, reviewer || undefined, note || undefined);
    onClose();
  };

  const handleCopy = (text: string) => {
    void navigator.clipboard.writeText(text);
  };

  return (
    <div className={`relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl animate-fade-in ${className}`}>
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className={`px-3 py-1.5 rounded-full border ${getDiffColor(diff.diff_type)}`}>
            <span className="font-medium">{getDiffLabel(diff.diff_type)}</span>
          </div>
          <span className="text-sm text-gray-500">ID: {diff.id}</span>
          {diff.reviewed ? (
            <div className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-800 rounded-full">
              <CheckCircle size={12} />
              <span className="text-xs font-medium">已審核</span>
            </div>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-full hover:bg-gray-100 transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      <div className="p-6">
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-500 mb-2">差異摘要</h4>
          <div
            className="rounded-2xl p-4 mb-4"
            style={{
              backgroundColor: 'rgba(255, 246, 190, 0.16)',
              border: '1px solid rgba(255, 221, 120, 0.50)',
            }}
          >
            <p className="text-sm text-gray-900 whitespace-pre-wrap break-words">
              {diff.diff_type === DiffType.IMAGE_DIFF
                ? '此範圍內偵測到視覺或排版變更（例如：圖片內容、表格外框、或文字位置移動），故無提取對應的純文字。'
                : diff.old_value && diff.new_value
                ? getTrimmedDiffText(diff.old_value, diff.new_value)
                : diff.new_value ?? diff.old_value ?? diff.context}
            </p>
          </div>

          <h4 className="text-sm font-medium text-gray-500 mb-2">位置</h4>
          <div className="flex items-center space-x-2">
            <ExternalLink size={16} className="text-gray-400" />
            <span className="text-gray-700">{diff.context}</span>
            {diff.confidence ? (
              <span className="text-xs px-2 py-1 bg-primary-50 text-primary-700 rounded">
                信度: {(diff.confidence * 100).toFixed(1)}%
              </span>
            ) : null}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-red-600">原始內容</h4>
              {diff.old_value ? (
                <button
                  type="button"
                  onClick={() => handleCopy(diff.old_value ?? '')}
                  className="p-1 rounded hover:bg-gray-100 transition-colors"
                  title="複製"
                >
                  <Copy size={14} className="text-gray-400" />
                </button>
              ) : null}
            </div>
            <div className={`p-4 rounded-lg border ${diff.old_value ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}`}>
              {diff.old_value ? (
                <pre className="text-sm text-gray-800 whitespace-pre-wrap break-words font-sans">
                  {diff.old_value}
                </pre>
              ) : (
                <p className="text-sm text-gray-500 italic">
                  {diff.diff_type === DiffType.IMAGE_DIFF ? '無原始文字（純視覺差異）' : '無原始內容'}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-green-600">修訂內容</h4>
              {diff.new_value ? (
                <button
                  type="button"
                  onClick={() => handleCopy(diff.new_value ?? '')}
                  className="p-1 rounded hover:bg-gray-100 transition-colors"
                  title="複製"
                >
                  <Copy size={14} className="text-gray-400" />
                </button>
              ) : null}
            </div>
            <div className={`p-4 rounded-lg border ${diff.new_value ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
              {diff.new_value ? (
                <pre className="text-sm text-gray-800 whitespace-pre-wrap break-words font-sans">
                  {diff.new_value}
                </pre>
              ) : (
                <p className="text-sm text-gray-500 italic">
                  {diff.diff_type === DiffType.IMAGE_DIFF ? '無修訂文字（純視覺差異）' : '無修訂內容'}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">審核人員</label>
            <input
              type="text"
              value={reviewer}
              onChange={(event) => setReviewer(event.target.value)}
              placeholder="輸入姓名或代號 (選填)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">備註</label>
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="輸入審核備註 (選填)"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-[#F5F5F5] rounded-b-2xl">
        <div className="text-sm text-gray-500">
          {diff.reviewed ? (
            <div className="flex items-center space-x-2">
              <CheckCircle size={14} className="text-green-500" />
              <span>已由 {diff.reviewed_by} 於 {diff.reviewed_at ? new Date(diff.reviewed_at).toLocaleString() : '未知時間'} 審核</span>
            </div>
          ) : (
            <span>尚未審核</span>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            關閉
          </button>
          <button
            type="button"
            onClick={handleFlag}
            className="px-4 py-2.5 border border-red-300 text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors flex items-center space-x-2"
          >
            <Flag size={16} />
            <span>標記問題</span>
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="px-4 py-2.5 bg-diff-added text-white rounded-lg hover:bg-emerald-600 transition-colors flex items-center space-x-2"
          >
            <CheckCircle size={16} />
            <span>確認此修改</span>
          </button>
        </div>
      </div>
    </div>
  );
};

const DiffPopup: React.FC<DiffPopupProps> = (props) => {
  const { diff, isOpen, onClose } = props;

  if (!isOpen || !diff) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/45"
        onClick={onClose}
      />
      <DiffPopupInner key={diff.id} {...props} diff={diff} />
    </div>
  );
};

export default DiffPopup;
