import React from 'react';
import { CheckCircle } from 'lucide-react';
import { DiffItem, DiffType } from '../services/types';

interface DiffListPanelProps {
  diffItems: DiffItem[];
  selectedDiffId: string | null;
  onDiffSelect: (diffId: string) => void;
  className?: string;
}

const getDiffIcon = (type: DiffType) => {
  switch (type) {
    case DiffType.ADDED:
      return <div className="w-3 h-3 rounded-full bg-diff-added" />;
    case DiffType.DELETED:
      return <div className="w-3 h-3 rounded-full bg-diff-deleted" />;
    case DiffType.NUMBER_MODIFIED:
      return <div className="w-3 h-3 rounded-full bg-diff-modified" />;
    case DiffType.TEXT_MODIFIED:
      return <div className="w-3 h-3 rounded-full bg-diff-text" />;
    default:
      return <div className="w-3 h-3 rounded-full bg-gray-400" />;
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

const DiffListPanel: React.FC<DiffListPanelProps> = ({
  diffItems,
  selectedDiffId,
  onDiffSelect,
  className = '',
}) => {
  if (diffItems.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-full text-gray-500 space-y-2 p-6 ${className}`}>
        <p>目前沒有差異項目</p>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full overflow-hidden ${className}`}>
      <div className="flex-1 overflow-auto divide-y divide-gray-100">
        {diffItems.map((item) => {
          const isSelected = selectedDiffId === item.id;
          return (
            <div
              key={item.id}
              className={`p-3 cursor-pointer transition-colors ${
                isSelected ? 'bg-primary-50 border-l-4 border-l-primary-500' : 'hover:bg-gray-50 border-l-4 border-l-transparent'
              } ${item.reviewed ? 'opacity-60 saturate-50' : ''}`}
              onClick={() => onDiffSelect(item.id)}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {getDiffIcon(item.diff_type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      {getDiffLabel(item.diff_type)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {item.context}
                    </span>
                    {item.reviewed && (
                      <CheckCircle className="text-green-500" size={14} />
                    )}
                  </div>
                  
                  <div className="space-y-1">
                    {item.old_value && (
                      <div className="flex items-center">
                        <span className="text-xs text-red-600 bg-red-50 px-1.5 py-0.5 rounded mr-2 flex-shrink-0">
                          舊值
                        </span>
                        <p className={`text-sm ${item.reviewed ? 'text-gray-500' : 'text-gray-700'} line-clamp-2`}>
                          {item.old_value}
                        </p>
                      </div>
                    )}
                    
                    {item.new_value && (
                      <div className="flex items-center">
                        <span className="text-xs text-green-600 bg-green-50 px-1.5 py-0.5 rounded mr-2 flex-shrink-0">
                          新值
                        </span>
                        <p className={`text-sm ${item.reviewed ? 'text-gray-500' : 'text-gray-700'} line-clamp-2`}>
                          {item.new_value}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DiffListPanel;
