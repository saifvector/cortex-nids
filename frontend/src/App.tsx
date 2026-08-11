import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { LiveThreats } from './pages/LiveThreats';
import { HistoricalThreats } from './pages/HistoricalThreats';
import { HistoricalAnalytics } from './pages/HistoricalAnalytics';
import { Prediction } from './pages/Prediction';
import { BatchAnalysis } from './pages/BatchAnalysis';
import { FeatureImportance } from './pages/FeatureImportance';
import { ModelInsights } from './pages/ModelInsights';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  return (
    <Router>
      <div className="relative min-h-screen bg-[#04070E] text-slate-100 font-sans antialiased overflow-hidden">
        {/* Ambient Aurora Orbs */}
        <div className="aurora-bg">
          <div className="orb-1" />
          <div className="orb-2" />
          <div className="orb-3" />
        </div>

        {/* Content Container */}
        <div className="relative z-10 flex min-h-screen">
          {/* Permanent Floating Sidebar */}
          <Sidebar />

          {/* Main Layout Area */}
          <div className="flex-1 flex flex-col min-w-0">
            <Navbar />

            <main className="flex-1 p-6 md:p-8 overflow-y-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/live-threats" element={<LiveThreats />} />
                <Route path="/monitor" element={<LiveThreats />} />
                <Route path="/historical-threats" element={<HistoricalThreats />} />
                <Route path="/analytics" element={<HistoricalAnalytics />} />
                <Route path="/historical" element={<HistoricalAnalytics />} />
                <Route path="/predict" element={<Prediction />} />
                <Route path="/batch" element={<BatchAnalysis />} />
                <Route path="/features" element={<FeatureImportance />} />
                <Route path="/model" element={<ModelInsights />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </Router>
  );
};

export default App;
