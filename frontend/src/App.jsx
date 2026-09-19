import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, MemoryRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { LanguageProvider, useLanguage } from './hooks/useLanguage';
import PublicLayout from './layouts/PublicLayout';
import DashboardLayout from './layouts/DashboardLayout';
import LandingPage from './pages/LandingPage';
import ErrorBoundary from './components/ErrorBoundary';
import PwaLifecycle from './components/PwaLifecycle';
import { DataState } from './components/Experience';
import { dashboardFor } from './lib/session';
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const PricesPage = lazy(() => import('./pages/PricesPage'));
const CropPricePage = lazy(() => import('./pages/CropPricePage'));
const MandiDirectoryPage = lazy(() => import('./pages/MandiDirectoryPage'));
const MandiDetailPage = lazy(() => import('./pages/MandiDetailPage'));
const PublicBuyerDirectoryPage = lazy(() => import('./pages/PublicBuyerDirectoryPage'));
const InfoPage = lazy(() => import('./pages/InfoPage'));
const MapPage = lazy(() => import('./pages/MapPage'));
const FarmerDashboard = lazy(() => import('./pages/FarmerDashboard'));
const BuyerDashboard = lazy(() => import('./pages/BuyerDashboard'));
const BuyerRequirementsPage = lazy(() => import('./pages/BuyerRequirementsPage'));
const BuyerDiscoverPage = lazy(() => import('./pages/BuyerDiscoverPage'));
const FPODashboard = lazy(() => import('./pages/FPODashboard'));
const SellPage = lazy(() => import('./pages/SellPage'));
const OffersPage = lazy(() => import('./pages/OffersPage'));
const MatchesPage = lazy(() => import('./pages/MatchesPage'));
const TransactionsPage = lazy(() => import('./pages/TransactionsPage'));
const TradeRoomPage = lazy(() => import('./pages/TradeRoomPage'));
const GrievancesPage = lazy(() => import('./pages/GrievancesPage'));
const FarmerMorePage = lazy(() => import('./pages/FarmerMorePage'));
const FarmerPriceAlertsPage = lazy(() => import('./pages/FarmerPriceAlertsPage'));
const FarmerLotsPage = lazy(() => import('./pages/FarmerLotsPage'));
const FarmerLotDetailPage = lazy(() => import('./pages/FarmerLotsPage').then((module) => ({ default: module.FarmerLotDetailPage })));
const NotificationSettingsPage = lazy(() => import('./pages/NotificationSettingsPage'));
const AdminOperationsPage = lazy(() => import('./pages/AdminOperationsPage'));
export function ProtectedRoute({ roles, children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <DataState loading />;
  if (!user)
    return (
      <Navigate
        replace
        to={'/login?' + new URLSearchParams({ next: location.pathname + location.search })}
        state={{ from: location }}
      />
    );
  if (roles && !roles.includes(user.role)) return <Navigate replace to={dashboardFor(user.role)} />;
  return children;
}
export function RouteContent() {
  const location = useLocation();
  const { t } = useLanguage();
  useEffect(() => {
    if (location.hash) {
      requestAnimationFrame(() =>
        document.getElementById(location.hash.slice(1))?.scrollIntoView(),
      );
    } else window.scrollTo(0, 0);
  }, [location.pathname, location.hash]);
  return (
    <ErrorBoundary
      resetKey={location.pathname}
      title={t('server')}
      retry={t('retry')}
      home={t('returnHome')}
    >
      <PwaLifecycle />
      <Suspense fallback={<DataState loading />}>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/prices/:crop" element={<CropPricePage />} />
            <Route path="/prices" element={<PricesPage />} />
            <Route path="/mandis" element={<MandiDirectoryPage />} />
            <Route path="/mandis/:slug" element={<MandiDetailPage />} />
            <Route path="/buyers" element={<PublicBuyerDirectoryPage />} />
            <Route path="/map" element={<MapPage />} />
            {[
              'help', 'help/:slug', 'how-it-works', 'terms', 'privacy', 'refunds-and-cancellations',
              'grievance-policy', 'about', 'contact', 'accuracy', 'security', '404',
            ].map((path) => (
              <Route key={path} path={'/' + path} element={<InfoPage />} />
            ))}
            <Route path="*" element={<InfoPage />} />
          </Route>
          <Route
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/admin/operations" element={<ProtectedRoute roles={['admin', 'operator', 'support', 'reviewer', 'fraud_reviewer']}><AdminOperationsPage /></ProtectedRoute>} />
            <Route
              path="/farmer/dashboard"
              element={
                <ProtectedRoute roles={['farmer']}>
                  <FarmerDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/farmer/more"
              element={
                <ProtectedRoute roles={['farmer']}>
                  <FarmerMorePage />
                </ProtectedRoute>
              }
            />
            <Route path="/farmer/price-alerts" element={<ProtectedRoute roles={['farmer']}><FarmerPriceAlertsPage /></ProtectedRoute>} />
            <Route
              path="/farmer/lots"
              element={
                <ProtectedRoute roles={['farmer']}>
                  <FarmerLotsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/farmer/lots/:id"
              element={
                <ProtectedRoute roles={['farmer']}>
                  <FarmerLotDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/buyer/dashboard"
              element={
                <ProtectedRoute roles={['buyer']}>
                  <BuyerDashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/buyer/requirements" element={<ProtectedRoute roles={['buyer']}><BuyerRequirementsPage /></ProtectedRoute>} />
            <Route path="/buyer/discover" element={<ProtectedRoute roles={['buyer']}><BuyerDiscoverPage /></ProtectedRoute>} />
            <Route
              path="/fpo/dashboard"
              element={
                <ProtectedRoute roles={['fpo']}>
                  <FPODashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sell"
              element={
                <ProtectedRoute roles={['farmer', 'fpo']}>
                  <SellPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/matches"
              element={
                <ProtectedRoute roles={['farmer', 'fpo']}>
                  <MatchesPage />
                </ProtectedRoute>
              }
            />
            <Route path="/offers" element={<OffersPage />} />
            <Route path="/notification-settings" element={<NotificationSettingsPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/trades/:id" element={<TradeRoomPage />} />
            <Route path="/grievances" element={<GrievancesPage />} />
          </Route>
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}

const prerenderLoaders = [
  () => import('./pages/LoginPage'),
  () => import('./pages/RegisterPage'),
  () => import('./pages/PricesPage'),
  () => import('./pages/CropPricePage'),
  () => import('./pages/MandiDirectoryPage'),
  () => import('./pages/MandiDetailPage'),
  () => import('./pages/PublicBuyerDirectoryPage'),
  () => import('./pages/InfoPage'),
  () => import('./pages/MapPage'),
];
export async function preloadPrerenderRoutes() {
  await Promise.all(prerenderLoaders.map((load) => load()));
}

export function PrerenderApp({ path }) {
  return (
    <LanguageProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={[path]}>
          <RouteContent />
        </MemoryRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}
export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <RouteContent />
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}
