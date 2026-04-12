import React, { useCallback, useState } from 'react';
import { isAxiosError } from 'axios';
import { Upload, FileSpreadsheet, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { checklistApi } from '../services/api';
import { ChecklistImportResponse } from '../services/types';

interface ChecklistUploadProps {
  comparisonId: string;
  onUploadComplete?: (response: ChecklistImportResponse) => void;
  className?: string;
}

const allowedMimeTypes = [
  'text/csv',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
];

const ChecklistUpload: React.FC<ChecklistUploadProps> = ({
  comparisonId,
  onUploadComplete,
  className = '',
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<ChecklistImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): boolean => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    const isValidType = allowedMimeTypes.includes(file.type) ||
      extension === 'csv' ||
      extension === 'xlsx' ||
      extension === 'xls';

    if (!isValidType) {
      setError('請上傳 CSV 或 Excel 檔案 (支援 .csv, .xlsx, .xls)');
      return false;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB
      setError('檔案大小超過 10MB 限制');
      return false;
    }

    return true;
  }, []);

  const handleUpload = useCallback(
    async (file: File) => {
      if (!validateFile(file)) return;

      setIsUploading(true);
      setError(null);
      setUploadResult(null);

      try {
        const result = await checklistApi.importChecklist(comparisonId, file);
        setUploadResult(result);
        onUploadComplete?.(result);
      } catch (err: unknown) {
        const detail = isAxiosError<{ detail?: string }>(err) ? err.response?.data?.detail : undefined;
        setError(detail || '上傳失敗，請檢查檔案格式');
      } finally {
        setIsUploading(false);
      }
    },
    [comparisonId, onUploadComplete, validateFile]
  );

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleUpload(files[0]);
    }
  }, [handleUpload]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleUpload(files[0]);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Upload area */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        }`}
      >
        <input
          type="file"
          id="checklist-upload"
          className="hidden"
          accept=".csv,.xlsx,.xls,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          onChange={handleFileInput}
          disabled={isUploading}
        />

        <div className="flex flex-col items-center space-y-4">
          <div className={`p-4 rounded-full ${isUploading ? 'bg-blue-100' : 'bg-gray-100'}`}>
            {isUploading ? (
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
            ) : (
              <Upload size={32} className="text-gray-400" />
            )}
          </div>

          <div className="space-y-2">
            <h3 className="text-lg font-medium text-gray-900">
              上傳核對清單
            </h3>
            <p className="text-gray-600 max-w-md">
              拖放 CSV 或 Excel 檔案到此處，或點擊下方按鈕選擇檔案
            </p>
            <p className="text-sm text-gray-500">
              支援格式: CSV (.csv), Excel (.xlsx, .xls)
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <label
              htmlFor="checklist-upload"
              className={`px-6 py-3 rounded-lg font-medium transition-colors cursor-pointer ${
                isUploading
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-700'
              }`}
            >
              {isUploading ? '上傳中...' : '選擇檔案'}
            </label>
            <span className="text-gray-500">或</span>
            <button
              onClick={() => {
                // Example: download template
                const template = `item_id,check_type,search_keyword,expected_old,expected_new,page_hint
C001,number,保單利率,0.216%,0.195%,5
C002,text,解約費用,第一年解約費用,前三年解約費用,8
C003,general,重大疾病,包含癌症,包含癌症與心血管疾病,12`;
                const blob = new Blob([template], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'checklist_template.csv';
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              下載範本
            </button>
          </div>
        </div>

        {isDragging && (
          <div className="absolute inset-0 bg-primary-500/10 rounded-xl flex items-center justify-center">
            <div className="bg-white p-4 rounded-lg shadow-lg">
              <p className="text-primary-700 font-medium">放開以上傳檔案</p>
            </div>
          </div>
        )}
      </div>

      {/* File preview */}
      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 animate-fade-in">
          <div className="flex items-start space-x-4">
            <CheckCircle className="text-green-500 mt-1" size={24} />
            <div className="flex-1">
              <h4 className="text-lg font-medium text-green-800 mb-2">
                核對清單上傳成功
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-3 rounded-lg">
                  <div className="text-sm text-gray-500">項目總數</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {uploadResult.items_count}
                  </div>
                </div>
                <div className="bg-white p-3 rounded-lg">
                  <div className="text-sm text-gray-500">自動匹配</div>
                  <div className="text-2xl font-bold text-green-600">
                    {uploadResult.auto_matched_count}
                  </div>
                </div>
              </div>
              <p className="text-sm text-green-700 mt-3">
                系統已自動匹配 {uploadResult.auto_matched_count} 個項目到對應的差異。
                您可以在核對清單面板中檢視並確認剩餘項目。
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 animate-fade-in">
          <div className="flex items-start space-x-4">
            <AlertCircle className="text-red-500 mt-1" size={24} />
            <div className="flex-1">
              <h4 className="text-lg font-medium text-red-800 mb-2">
                上傳失敗
              </h4>
              <p className="text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm font-medium"
              >
                關閉錯誤訊息
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Format hints */}
      <div className="bg-[#F5F5F5] border border-gray-200 rounded-xl p-6">
        <h4 className="text-lg font-medium text-primary-800 mb-4 flex items-center">
          <FileSpreadsheet className="mr-2" size={20} />
          檔案格式說明
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h5 className="font-medium text-primary-700 mb-2">必要欄位</h5>
            <ul className="space-y-2 text-sm text-gray-800">
              <li className="flex items-center">
                <FileText size={14} className="mr-2" />
                <code className="bg-white px-2 py-0.5 rounded">item_id</code> - 項目唯一識別碼
              </li>
              <li className="flex items-center">
                <FileText size={14} className="mr-2" />
                <code className="bg-white px-2 py-0.5 rounded">search_keyword</code> - 搜尋關鍵字
              </li>
            </ul>
          </div>
          <div>
            <h5 className="font-medium text-primary-700 mb-2">選填欄位</h5>
            <ul className="space-y-2 text-sm text-gray-800">
              <li>
                <code className="bg-white px-2 py-0.5 rounded">expected_old</code> - 預期舊值
              </li>
              <li>
                <code className="bg-white px-2 py-0.5 rounded">expected_new</code> - 預期新值
              </li>
              <li>
                <code className="bg-white px-2 py-0.5 rounded">page_hint</code> - 頁面提示
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChecklistUpload;
