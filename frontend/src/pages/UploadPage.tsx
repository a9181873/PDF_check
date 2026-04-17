import React, { useState, useCallback, useEffect } from 'react';
import { isAxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';
import { Upload, File, Folder, AlertCircle, CheckCircle, XCircle, Clock, ChevronRight } from 'lucide-react';
import { compareApi, projectApi } from '../services/api';
import { ComparisonInfo } from '../services/types';

function getSuggestedProjectName(oldName: string, newName: string): string {
  const stripExt = (n: string) => n.replace(/\.pdf$/i, '');
  const a = stripExt(oldName);
  const b = stripExt(newName);
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  let common = a.substring(0, i).replace(/[-_\s()（）]+$/, '').trim();
  const today = new Date();
  const dateStr = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
  const timeStr = `${String(today.getHours()).padStart(2, '0')}${String(today.getMinutes()).padStart(2, '0')}${String(today.getSeconds()).padStart(2, '0')}`;
  return common ? `${common}_核對_${dateStr}_${timeStr}` : `PDF核對_${dateStr}_${timeStr}`;
}

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [oldFile, setOldFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);
  const [projectId, setProjectId] = useState('');
  const [projectIdUserEdited, setProjectIdUserEdited] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [recentComparisons, setRecentComparisons] = useState<ComparisonInfo[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const history = await projectApi.listAllComparisons(5);
        setRecentComparisons(history);
      } catch (err) {
        console.error('Failed to fetch history:', err);
      } finally {
        setIsLoadingHistory(false);
      }
    };
    fetchHistory();
  }, []);

  // Auto-suggest project name when both files are selected (only if user hasn't edited)
  useEffect(() => {
    if (oldFile && newFile && !projectIdUserEdited) {
      setProjectId(getSuggestedProjectName(oldFile.name, newFile.name));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [oldFile, newFile]);

  const validateFile = (file: File): boolean => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('僅支援 PDF 檔案格式');
      return false;
    }
    if (file.size > 50 * 1024 * 1024) { // 50MB
      setError('檔案大小超過 50MB 限制');
      return false;
    }
    return true;
  };

  const handleFileSelect = (side: 'old' | 'new', files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    const file = files[0];
    if (!validateFile(file)) return;
    
    setError(null);
    if (side === 'old') {
      setOldFile(file);
    } else {
      setNewFile(file);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent, side: 'old' | 'new') => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        setError(null);
        if (side === 'old') {
          setOldFile(file);
        } else {
          setNewFile(file);
        }
      }
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!oldFile || !newFile) {
      setError('請選擇舊版與新版 PDF 檔案');
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await compareApi.uploadFiles(oldFile, newFile, projectId || undefined);
      setSuccess('檔案上傳成功！正在進行比對分析...');
      
      // Redirect to compare page after a short delay
      setTimeout(() => {
        navigate(`/compare/${result.task_id}`);
      }, 1500);
    } catch (err: unknown) {
      const detail = isAxiosError<{ detail?: string }>(err) ? err.response?.data?.detail : undefined;
      setError(detail || '上傳失敗，請稍後再試');
    } finally {
      setIsUploading(false);
    }
  };

  const FileUploadArea = ({ side, label, file }: { side: 'old' | 'new'; label: string; file: File | null }) => (
    <div
      onDrop={(e) => handleDrop(e, side)}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
        isDragging ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
      }`}
    >
      <input
        type="file"
        id={`${side}-upload`}
        className="hidden"
        accept=".pdf"
        onChange={(e) => handleFileSelect(side, e.target.files)}
        disabled={isUploading}
      />
      
      {file ? (
        <div className="space-y-4">
          <div className="flex items-center justify-center">
            <div className="p-3 bg-green-100 rounded-full">
              <CheckCircle className="text-green-600" size={32} />
            </div>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-1">{label} 已選擇</h3>
            <div className="flex items-center justify-center space-x-2 text-gray-600">
              <File size={16} />
              <span className="text-sm truncate max-w-xs">{file.name}</span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          <button
            type="button"
            onClick={() => side === 'old' ? setOldFile(null) : setNewFile(null)}
            className="px-4 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
            disabled={isUploading}
          >
            移除檔案
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-center">
            <div className="p-3 bg-gray-100 rounded-full">
              <Upload className="text-gray-400" size={32} />
            </div>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-1">{label}</h3>
            <p className="text-gray-600">拖放 PDF 檔案到此處，或點擊選擇檔案</p>
          </div>
          <label
            htmlFor={`${side}-upload`}
            className={`inline-block px-6 py-3 rounded-lg font-medium transition-colors cursor-pointer ${
              isUploading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            }`}
          >
            選擇檔案
          </label>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(0,153,68,0.10),_transparent_38%),linear-gradient(180deg,_#f5f5f5_0%,_#eef4ef_100%)] flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center rounded-full border border-primary-200 bg-white/80 px-4 py-1.5 text-sm font-medium text-primary-700 shadow-soft backdrop-blur">
            Smart PDF Review
          </div>
          <h1 className="mt-4 text-4xl font-bold tracking-tight text-gray-900 mb-3">PDF 差異比對系統</h1>
          <p className="text-gray-600 max-w-2xl mx-auto leading-7">
            上傳新舊版保險 DM 檔案，系統將自動比對文字與數字差異，並在灰階化的 PDF 上以彩色標記呈現。
          </p>
        </div>

        {/* Upload form */}
        <div className="bg-white/95 rounded-[28px] shadow-large border border-white p-8 backdrop-blur">
          <form onSubmit={handleSubmit}>
            {/* Project selection */}
            <div className="mb-8">
              <div className="flex items-center space-x-2 mb-3">
                <Folder className="text-gray-400" size={20} />
                <h2 className="text-lg font-medium text-gray-900">專案設定 (選填)</h2>
              </div>
              <input
                type="text"
                value={projectId}
                onChange={(e) => { setProjectId(e.target.value); setProjectIdUserEdited(true); }}
                placeholder="上傳兩個檔案後將自動帶入共通名稱+核對日期時間"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-sm text-gray-500 mt-2">
                選取兩個檔案後自動以共通檔名＋核對日期時間建議，可手動修改。
              </p>
            </div>

            {/* File upload areas */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <FileUploadArea
                side="old"
                label="舊版 PDF"
                file={oldFile}
              />
              <FileUploadArea
                side="new"
                label="新版 PDF"
                file={newFile}
              />
            </div>

            {/* Status messages */}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-6 animate-fade-in">
                <div className="flex items-start space-x-4">
                  <AlertCircle className="text-red-500 mt-1" size={24} />
                  <div className="flex-1">
                    <h4 className="text-lg font-medium text-red-800 mb-2">上傳失敗</h4>
                    <p className="text-red-700">{error}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setError(null)}
                    className="p-2 rounded-full hover:bg-red-100 transition-colors"
                  >
                    <XCircle className="text-red-500" size={20} />
                  </button>
                </div>
              </div>
            )}

            {success && (
              <div className="mb-6 bg-green-50 border border-green-200 rounded-xl p-6 animate-fade-in">
                <div className="flex items-start space-x-4">
                  <CheckCircle className="text-green-500 mt-1" size={24} />
                  <div className="flex-1">
                    <h4 className="text-lg font-medium text-green-800 mb-2">上傳成功</h4>
                    <p className="text-green-700">{success}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Submit button */}
            <div className="flex items-center justify-between gap-6">
              <div className="text-sm text-gray-600">
                <p>支援 PDF 檔案格式，單一檔案最大 50MB</p>
                <p>比對過程可能需要數分鐘，視檔案大小而定</p>
              </div>
              <button
                type="submit"
                disabled={!oldFile || !newFile || isUploading}
                className={`px-8 py-4 rounded-lg font-medium text-lg transition-all ${
                  !oldFile || !newFile || isUploading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-primary-600 text-white hover:bg-primary-700 shadow-lg hover:shadow-xl'
                }`}
              >
                {isUploading ? (
                  <div className="flex items-center space-x-3">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>上傳與比對中...</span>
                  </div>
                ) : (
                  '開始比對'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* History Section */}
        {recentComparisons.length > 0 && (
          <div className="mt-8 bg-white/95 rounded-[28px] shadow-large border border-white p-8 backdrop-blur">
            <div className="flex items-center space-x-2 mb-6">
              <Clock className="text-gray-400" size={24} />
              <h2 className="text-xl font-bold text-gray-900">最近比對紀錄</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recentComparisons.map((comp) => (
                <div
                  key={comp.id}
                  onClick={() => navigate(`/compare/${comp.id}`)}
                  className="group relative flex items-center p-4 bg-gray-50 hover:bg-primary-50 rounded-2xl border border-gray-100 hover:border-primary-100 cursor-pointer transition-all hover:shadow-md"
                >
                  <div className="flex-1 min-w-0 pr-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded-md shadow-sm border border-gray-100">
                        {new Date(comp.created_at).toLocaleDateString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {comp.status === 'done' ? (
                        <span className="text-xs text-green-600 font-medium">已完成</span>
                      ) : comp.status === 'error' ? (
                        <span className="text-xs text-red-600 font-medium">錯誤</span>
                      ) : (
                        <span className="text-xs text-blue-600 font-medium animate-pulse">處理中</span>
                      )}
                    </div>
                    <div className="mt-2 space-y-1">
                      <div className="flex items-start space-x-2">
                        <span className="text-xs text-gray-400 mt-0.5">舊:</span>
                        <p className="text-sm text-gray-700 truncate font-medium">{comp.old_filename}</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <span className="text-xs text-gray-400 mt-0.5">新:</span>
                        <p className="text-sm text-gray-700 truncate font-medium">{comp.new_filename}</p>
                      </div>
                    </div>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all shadow-sm">
                    <ChevronRight size={18} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Features grid */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/90 p-6 rounded-2xl border border-white shadow-soft">
            <div className="w-12 h-12 bg-primary-50 rounded-2xl flex items-center justify-center mb-4">
              <span className="text-primary-700 font-bold">1</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">雙欄同步視圖</h3>
            <p className="text-gray-600 text-sm">
              左右並排顯示新舊檔案，滾動自動同步，可隱藏左側面板專注新版內容。
            </p>
          </div>
          <div className="bg-white/90 p-6 rounded-2xl border border-white shadow-soft">
            <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mb-4">
              <span className="text-primary-700 font-bold">2</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">空間映射標記</h3>
            <p className="text-gray-600 text-sm">
              灰階 PDF 上疊加彩色差異標記（橘色數值、綠色新增），保持閱讀語境。
            </p>
          </div>
          <div className="bg-white/90 p-6 rounded-2xl border border-white shadow-soft">
            <div className="w-12 h-12 bg-primary-100 rounded-2xl flex items-center justify-center mb-4">
              <span className="text-primary-700 font-bold">3</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">智慧核對清單</h3>
            <p className="text-gray-600 text-sm">
              上傳 CSV/Excel 核對清單，系統自動匹配差異項目，加速審核流程。
            </p>
          </div>
        </div>

        {/* Footer note */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>系統使用 AI 文件解析技術，自動比對文字與數字差異，專為保險 DM 審核設計。</p>
          <p className="mt-1">資料僅儲存於本地，確保敏感資訊安全。</p>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
