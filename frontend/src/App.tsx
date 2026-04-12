import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

const UploadPage = lazy(() => import('./pages/UploadPage'));
const ComparePage = lazy(() => import('./pages/ComparePage'));

function RouteFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[linear-gradient(180deg,_#f5f5f5_0%,_#eef4ef_100%)]">
      <div className="text-center">
        <div className="w-12 h-12 mx-auto mb-4 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm tracking-[0.18em] uppercase text-primary-700">Loading workspace</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/compare/:taskId" element={<ComparePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
