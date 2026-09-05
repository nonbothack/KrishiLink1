// =============================================================
// FPO Dashboard
// Farmer Producer Organization dashboard with aggregation
// =============================================================

import { useState } from 'react';
import { Users, Package, TrendingUp, CheckCircle2, Plus, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { createLot } from '../services/api';

// Demo FPO aggregation data
const FPO_FARMERS = [
  { name: 'Ramesh Patil',    location: 'Lasalgaon', crop: 'Onion', quantity: 200, grade: 'A' },
  { name: 'Sunita Deshpande',location: 'Nashik',    crop: 'Onion', quantity: 300, grade: 'A' },
  { name: 'Ganesh Shinde',   location: 'Sinnar',    crop: 'Onion', quantity: 500, grade: 'B' },
  { name: 'Laxmi Jadhav',    location: 'Nashik',    crop: 'Onion', quantity: 200, grade: 'A' },
];

function SummaryCard({ title, value, icon: Icon, color }) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center flex-shrink-0`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export default function FPODashboard() {
  const { user } = useAuth();
  const { t, cropT } = useLanguage();
  const [selected, setSelected] = useState(FPO_FARMERS.map((_, i) => i));
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState(false);

  const selectedFarmers = FPO_FARMERS.filter((_, i) => selected.includes(i));
  const totalQty = selectedFarmers.reduce((s, f) => s + f.quantity, 0);
  const predominantCrop = 'Onion'; // simplified
  const hasGradeA = selectedFarmers.some(f => f.grade === 'A');

  const toggleFarmer = (i) => {
    setSelected(prev => prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i]);
  };

  const handleCreateAggregatedLot = async () => {
    setCreating(true);
    await createLot({
      crop: predominantCrop,
      quantity: totalQty,
      unit: 'Quintal',
      grade: hasGradeA ? 'A' : 'B',
      location: 'Nashik',
      expected_price: 1850,
      notes: `Aggregated lot from ${selectedFarmers.length} FPO members`,
    });
    setCreating(false);
    setCreated(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('fpoDashboard')}</h1>
        <p className="text-gray-500 text-sm mt-1">{user?.name || 'Nashik Farmer Collective FPO'}</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard title={t('totalMembers')} value="120" icon={Users} color="bg-green-100 text-green-700" />
        <SummaryCard title={t('activeLots')} value="3" icon={Package} color="bg-blue-100 text-blue-700" />
        <SummaryCard title={t('pendingOffers')} value="2" icon={TrendingUp} color="bg-amber-100 text-amber-700" />
        <SummaryCard title={t('completedSales')} value="8" icon={CheckCircle2} color="bg-purple-100 text-purple-700" />
      </div>

      {/* Aggregation Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{t('produceAggregation')}</h2>
            <p className="text-gray-500 text-sm mt-0.5">
              {t('aggregationSubtitle')}
            </p>
          </div>
        </div>

        {/* Farmer selection */}
        <div className="space-y-3 mb-6">
          {FPO_FARMERS.map((farmer, i) => (
            <label
              key={i}
              className={`flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all ${
                selected.includes(i)
                  ? 'border-green-600 bg-green-50'
                  : 'border-gray-200 hover:border-green-300 bg-white'
              }`}
            >
              <input
                type="checkbox"
                checked={selected.includes(i)}
                onChange={() => toggleFarmer(i)}
                className="w-4 h-4 accent-green-700"
              />
              <div className="flex-1">
                <p className="font-semibold text-gray-800">{farmer.name}</p>
                <p className="text-sm text-gray-500">{farmer.location}</p>
              </div>
              <div className="text-right">
                <p className="font-bold text-gray-900">{farmer.quantity} {t('quintal')}</p>
                <p className="text-xs text-gray-500">{t('grade')} {farmer.grade} {cropT(farmer.crop)}</p>
              </div>
            </label>
          ))}
        </div>

        {/* Aggregation summary */}
        <div className="bg-green-50 border border-green-200 rounded-2xl p-5 mb-5">
          <h3 className="font-bold text-green-800 mb-3">{t('aggregatedLotPreview')}</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-3xl font-bold text-green-800">{totalQty}</p>
              <p className="text-sm text-gray-600">{t('totalQuintals')}</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-green-800">{selectedFarmers.length}</p>
              <p className="text-sm text-gray-600">{t('farmers')}</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-green-800">{cropT(predominantCrop)}</p>
              <p className="text-sm text-gray-600">{t('crop')}</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-green-800">
                ₹{(totalQty * 1850).toLocaleString('en-IN')}
              </p>
              <p className="text-sm text-gray-600">{t('estValue')}</p>
            </div>
          </div>
          <div className="mt-3 bg-white rounded-xl p-3 text-sm text-gray-600">
            <p className="font-medium text-green-700 mb-1">{t('whyAggregate')}</p>
            <p>{t('whyAggregateDesc')}</p>
          </div>
        </div>

        {created ? (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4">
            <div className="flex items-center gap-2 text-green-700 font-semibold">
              <CheckCircle2 className="w-5 h-5" />
              {t('aggregatedLotCreated')}
            </div>
            <Link to="/matches" className="btn-primary btn-sm flex items-center gap-2 ml-auto">
              {t('findBuyers')} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <button
            onClick={handleCreateAggregatedLot}
            disabled={creating || selectedFarmers.length === 0}
            className="btn-primary flex items-center gap-2 disabled:opacity-60"
          >
            <Plus className="w-5 h-5" />
            {creating ? t('loading') : `${t('createAggregatedLot')} (${totalQty} ${t('quintal')})`}
          </button>
        )}
      </div>

      {/* Quick links */}
      <div className="grid sm:grid-cols-3 gap-4">
        <Link to="/prices" className="card-hover flex items-center gap-3 group">
          <TrendingUp className="w-8 h-8 text-green-600" />
          <div>
            <p className="font-semibold text-gray-800">{t('marketPrices')}</p>
            <p className="text-xs text-gray-500">{t('todaysMandiRates')}</p>
          </div>
        </Link>
        <Link to="/offers" className="card-hover flex items-center gap-3 group">
          <Package className="w-8 h-8 text-blue-600" />
          <div>
            <p className="font-semibold text-gray-800">{t('offers')}</p>
            <p className="text-xs text-gray-500">{t('viewBuyerOffers')}</p>
          </div>
        </Link>
        <Link to="/map" className="card-hover flex items-center gap-3 group">
          <Users className="w-8 h-8 text-purple-600" />
          <div>
            <p className="font-semibold text-gray-800">{t('map')}</p>
            <p className="text-xs text-gray-500">{t('findMandisBuyers')}</p>
          </div>
        </Link>
      </div>
    </div>
  );
}
