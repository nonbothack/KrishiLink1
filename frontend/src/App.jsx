// =============================================================
// KrishiLink Main App
// Sets up routing and provides global context to all pages
// =============================================================

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { LanguageProvider } from './hooks/useLanguage';

// Layouts
import PublicLayout from './layouts/PublicLayout';
import DashboardLayout from './layouts/DashboardLayout';

// Public pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PricesPage from './pages/PricesPage';
import MapPage from './pages/MapPage';

// Dashboard pages
import FarmerDashboard from './pages/FarmerDashboard';
import BuyerDashboard from './pages/BuyerDashboard';
import FPODashboard from './pages/FPODashboard';
import SellPage from './pages/SellPage';
import MatchesPage from './pages/MatchesPage';
import OffersPage from './pages/OffersPage';
import TransactionsPage from './pages/TransactionsPage';
import GrievancesPage from './pages/GrievancesPage';
import TradeRoomPage from './pages/TradeRoomPage';

// Protected route: redirects to login if not logged in
function ProtectedRoute({ children, requiredRole = null }) {
  const { isLoggedIn, user } = useAuth();

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    // Redirect to appropriate dashboard based on role
    if (user?.role === 'farmer') return <Navigate to="/farmer/dashboard" replace />;
    if (user?.role === 'buyer') return <Navigate to="/buyer/dashboard" replace />;
    if (user?.role === 'fpo') return <Navigate to="/fpo/dashboard" replace />;
  }

  return children;
}

function App() {
  return (
    // LanguageProvider and AuthProvider wrap everything
    // so every component can access language and user state
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* ---- PUBLIC ROUTES (no login required) ---- */}
            <Route element={<PublicLayout />}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/prices" element={<PricesPage />} />
              <Route path="/map" element={<MapPage />} />
            </Route>

            {/* ---- FARMER ROUTES ---- */}
            <Route element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }>
              <Route path="/farmer/dashboard" element={<FarmerDashboard />} />
              <Route path="/sell" element={<SellPage />} />
              <Route path="/matches" element={<MatchesPage />} />
              <Route path="/offers" element={<OffersPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/trades/:id" element={<TradeRoomPage />} />
              <Route path="/grievances" element={<GrievancesPage />} />
            </Route>

            {/* ---- BUYER ROUTES ---- */}
            <Route element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }>
              <Route path="/buyer/dashboard" element={<BuyerDashboard />} />
            </Route>

            {/* ---- FPO ROUTES ---- */}
            <Route element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }>
              <Route path="/fpo/dashboard" element={<FPODashboard />} />
            </Route>

            {/* ---- REDIRECT UNKNOWN ROUTES ---- */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
