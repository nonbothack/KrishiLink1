// =============================================================
// FPO Dashboard
// Production-Ready Farmer Producer Organization Portal
// Live Aggregation, Member Management, Lots & Offers Tracking
// =============================================================

import { useState, useEffect } from 'react';
import {
  Users,
  Package,
  TrendingUp,
  CheckCircle2,
  Plus,
  ArrowRight,
  RefreshCw,
  Search,
  ShieldCheck,
  DollarSign,
  Layers,
  MapPin,
  X,
  Phone,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import {
  getFPOSummary,
  getFPOMembers,
  addFPOMember,
  getFPOLots,
  createFPOAggregatedLot,
  getLivePrices,
} from '../services/api';
import Tilt3DCard from '../components/visual/Tilt3DCard';

function SummaryCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <Tilt3DCard className="h-full">
      <div className="card flex items-start gap-4 h-full">
        <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center flex-shrink-0`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm text-gray-500 font-medium truncate">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-0.5 truncate">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-0.5 truncate">{subtitle}</p>}
        </div>
      </div>
    </Tilt3DCard>
  );
}

export default function FPODashboard() {
  const { user } = useAuth();
  const { t, cropT } = useLanguage();

  // Active Tab: 'aggregation' | 'lots' | 'members'
  const [activeTab, setActiveTab] = useState('aggregation');

  // Live state
  const [summary, setSummary] = useState(null);
  const [members, setMembers] = useState([]);
  const [lots, setLots] = useState([]);
  const [mandiPrices, setMandiPrices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Aggregation selection state
  const [selectedMemberIds, setSelectedMemberIds] = useState([]);
  const [aggCrop, setAggCrop] = useState('Onion');
  const [aggAskingPrice, setAggAskingPrice] = useState('1950');
  const [aggLocation, setAggLocation] = useState('Nashik FPO Central Hub');
  const [aggGrade, setAggGrade] = useState('A');
  const [aggNotes, setAggNotes] = useState('');
  const [creatingLot, setCreatingLot] = useState(false);
  const [createdLotSuccess, setCreatedLotSuccess] = useState(null);
  const [aggError, setAggError] = useState('');

  // Member Search & Add Modal
  const [searchMember, setSearchMember] = useState('');
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [newMember, setNewMember] = useState({
    farmer_name: '',
    phone: '',
    village: '',
    district: 'Nashik',
    land_acres: '',
    primary_crop: 'Onion',
    ready_quantity_qtl: '',
    grade: 'A',
  });
  const [addingMember, setAddingMember] = useState(false);
  const [memberActionMsg, setMemberActionMsg] = useState('');

  // Initial Data Fetching
  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [sumRes, memRes, lotRes, priceRes] = await Promise.all([
        getFPOSummary(),
        getFPOMembers(),
        getFPOLots(),
        getLivePrices({ limit: 100, state: 'Maharashtra' }),
      ]);

      if (sumRes.success && sumRes.data) {
        setSummary(sumRes.data);
      }
      if (memRes.success && Array.isArray(memRes.data)) {
        setMembers(memRes.data);
        // Preselect all members matching predominant crop
        const matchingIds = memRes.data
          .filter((m) => m.primary_crop.toLowerCase() === aggCrop.toLowerCase())
          .map((m) => m.id);
        setSelectedMemberIds(matchingIds.length > 0 ? matchingIds : memRes.data.slice(0, 3).map((m) => m.id));
      }
      if (lotRes.success && Array.isArray(lotRes.data)) {
        setLots(lotRes.data);
      }
      if (priceRes.success && Array.isArray(priceRes.data)) {
        setMandiPrices(priceRes.data);
      }
    } catch (err) {
      console.error('Failed to load FPO dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Update selected member filter when crop changes
  const handleCropChange = (crop) => {
    setAggCrop(crop);
    const matching = members.filter((m) => m.primary_crop.toLowerCase() === crop.toLowerCase()).map((m) => m.id);
    setSelectedMemberIds(matching);

    // Update benchmark price recommendation
    const matchingPrice = mandiPrices.find((p) => p.crop?.toLowerCase() === crop.toLowerCase());
    if (matchingPrice && matchingPrice.modal_price) {
      setAggAskingPrice(String(matchingPrice.modal_price));
    }
  };

  const toggleMemberSelection = (id) => {
    setSelectedMemberIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  // Selected farmers calculation
  const selectedMembers = members.filter((m) => selectedMemberIds.includes(m.id));
  const totalAggregatedQty = selectedMembers.reduce(
    (acc, m) => acc + (Number(m.ready_quantity_qtl) || 0),
    0
  );
  const estLotValue = totalAggregatedQty * (Number(aggAskingPrice) || 0);

  // Publish Aggregated Lot
  const handleCreateAggregatedLot = async (e) => {
    e.preventDefault();
    if (totalAggregatedQty <= 0) {
      setAggError('Please select at least one member with ready produce quantity.');
      return;
    }
    setAggError('');
    setCreatingLot(true);
    const res = await createFPOAggregatedLot({
      crop: aggCrop,
      quantity: totalAggregatedQty,
      unit: 'quintal',
      grade: aggGrade,
      asking_price: Number(aggAskingPrice) || 1950,
      location_text: aggLocation,
      district: 'Nashik',
      member_ids: selectedMemberIds,
      notes: aggNotes || `Aggregated bulk lot from ${selectedMembers.length} FPO members`,
    });
    setCreatingLot(false);

    if (res.success && res.data) {
      setCreatedLotSuccess(res.data);
      // Refresh lots and summary
      loadDashboardData();
    } else {
      setAggError(res.error || 'Failed to publish collective lot.');
    }
  };

  // Register New Member
  const handleAddMemberSubmit = async (e) => {
    e.preventDefault();
    setAddingMember(true);
    setMemberActionMsg('');
    const res = await addFPOMember({
      farmer_name: newMember.farmer_name,
      phone: newMember.phone || null,
      village: newMember.village || null,
      district: newMember.district || 'Nashik',
      land_acres: Number(newMember.land_acres) || 0,
      primary_crop: newMember.primary_crop,
      ready_quantity_qtl: Number(newMember.ready_quantity_qtl) || 0,
      grade: newMember.grade,
    });
    setAddingMember(false);
    if (res.success) {
      setShowAddMemberModal(false);
      setNewMember({
        farmer_name: '',
        phone: '',
        village: '',
        district: 'Nashik',
        land_acres: '',
        primary_crop: 'Onion',
        ready_quantity_qtl: '',
        grade: 'A',
      });
      loadDashboardData();
    } else {
      setMemberActionMsg(res.error || 'Failed to add member.');
    }
  };

  const filteredMembers = members.filter(
    (m) =>
      m.farmer_name.toLowerCase().includes(searchMember.toLowerCase()) ||
      (m.village && m.village.toLowerCase().includes(searchMember.toLowerCase())) ||
      m.primary_crop.toLowerCase().includes(searchMember.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">{t('fpoDashboard') || 'FPO Dashboard'}</h1>
            <span className="bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-green-700" />
              Verified Collective
            </span>
          </div>
          <p className="text-gray-500 text-sm mt-1">
            {summary?.organization_name || user?.name || 'Nashik Farmer Collective FPO'} ·{' '}
            <span className="text-gray-400">Reg: {summary?.registration_number || 'MH-FPO-09112'}</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => loadDashboardData()}
            className="btn-secondary btn-sm flex items-center gap-1.5"
            title="Refresh dashboard metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <button
            onClick={() => setShowAddMemberModal(true)}
            className="btn-primary btn-sm flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Add Member</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title={t('totalMembers') || 'Total Members'}
          value={summary?.total_members || '120'}
          subtitle="Registered farmers"
          icon={Users}
          color="bg-green-100 text-green-700"
        />
        <SummaryCard
          title="Aggregated Volume"
          value={`${summary?.total_volume_qtl || 0} qtl`}
          subtitle={`${summary?.active_lots || 0} active bulk lots`}
          icon={Package}
          color="bg-blue-100 text-blue-700"
        />
        <SummaryCard
          title={t('pendingOffers') || 'Pending Offers'}
          value={summary?.pending_offers || '0'}
          subtitle={`₹${(summary?.pending_offers_value || 0).toLocaleString('en-IN')} value`}
          icon={TrendingUp}
          color="bg-amber-100 text-amber-700"
        />
        <SummaryCard
          title="Completed Sales"
          value={`₹${(summary?.total_revenue || 0).toLocaleString('en-IN')}`}
          subtitle={`${summary?.completed_deals || 0} deals finalized`}
          icon={CheckCircle2}
          color="bg-purple-100 text-purple-700"
        />
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('aggregation')}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
              activeTab === 'aggregation'
                ? 'border-green-600 text-green-700 font-semibold'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Layers className="w-4 h-4" />
            Produce Aggregation Hub
          </button>

          <button
            onClick={() => setActiveTab('lots')}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
              activeTab === 'lots'
                ? 'border-green-600 text-green-700 font-semibold'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Package className="w-4 h-4" />
            Published Lots & Offers ({lots.length})
          </button>

          <button
            onClick={() => setActiveTab('members')}
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
              activeTab === 'members'
                ? 'border-green-600 text-green-700 font-semibold'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Users className="w-4 h-4" />
            Member Farmers ({members.length})
          </button>
        </nav>
      </div>

      {/* TAB 1: PRODUCE AGGREGATION HUB */}
      {activeTab === 'aggregation' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Member Selection List (2 cols on desktop) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="card">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">{t('produceAggregation') || 'Produce Aggregation'}</h2>
                  <p className="text-gray-500 text-xs mt-0.5">
                    Select verified member harvests to aggregate into a single high-value lot.
                  </p>
                </div>

                {/* Filter by crop */}
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-gray-500">Filter Crop:</span>
                  <select
                    value={aggCrop}
                    onChange={(e) => handleCropChange(e.target.value)}
                    className="input text-xs py-1.5 px-2.5 rounded-lg border-gray-300"
                  >
                    <option value="Onion">Onion</option>
                    <option value="Tomato">Tomato</option>
                    <option value="Soybean">Soybean</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Cotton">Cotton</option>
                  </select>
                </div>
              </div>

              {/* Members checkboxes */}
              <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
                {members.length === 0 ? (
                  <p className="text-center py-8 text-sm text-gray-400">
                    No members registered. Click &quot;Add Member&quot; to onboard farmers.
                  </p>
                ) : (
                  members.map((farmer) => {
                    const isSelected = selectedMemberIds.includes(farmer.id);
                    return (
                      <label
                        key={farmer.id}
                        className={`flex items-center gap-3.5 p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                          isSelected
                            ? 'border-green-600 bg-green-50/70 shadow-sm'
                            : 'border-gray-200 hover:border-gray-300 bg-white'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleMemberSelection(farmer.id)}
                          className="w-4 h-4 accent-green-700 rounded"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-gray-900 text-sm truncate">{farmer.farmer_name}</p>
                            <span className="text-[11px] px-1.5 py-0.2 bg-gray-100 text-gray-600 rounded">
                              {farmer.village || farmer.district || 'Nashik'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {farmer.land_acres} acres · {cropT(farmer.primary_crop)} · Grade {farmer.grade}
                          </p>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="font-bold text-gray-900 text-sm">
                            {farmer.ready_quantity_qtl} <span className="text-xs font-normal text-gray-500">qtl</span>
                          </p>
                          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                            isSelected ? 'bg-green-200 text-green-800' : 'bg-gray-100 text-gray-500'
                          }`}>
                            {isSelected ? 'Aggregated' : 'Available'}
                          </span>
                        </div>
                      </label>
                    );
                  })
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                <span>{selectedMembers.length} of {members.length} members selected</span>
                <button
                  type="button"
                  onClick={() => setSelectedMemberIds(members.map((m) => m.id))}
                  className="text-green-700 font-semibold hover:underline"
                >
                  Select All
                </button>
              </div>
            </div>
          </div>

          {/* Aggregation Summary & Publish Form (1 col) */}
          <div className="space-y-4">
            <div className="card bg-gradient-to-br from-green-50/90 to-white border-green-200">
              <h3 className="font-bold text-green-900 text-base mb-3 flex items-center gap-2">
                <Package className="w-5 h-5 text-green-700" />
                Aggregated Lot Preview
              </h3>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-white p-3 rounded-xl border border-green-100 shadow-2xs">
                  <span className="text-xs text-gray-500">Total Volume</span>
                  <p className="text-xl font-bold text-green-800">{totalAggregatedQty} qtl</p>
                </div>
                <div className="bg-white p-3 rounded-xl border border-green-100 shadow-2xs">
                  <span className="text-xs text-gray-500">Farmers Included</span>
                  <p className="text-xl font-bold text-green-800">{selectedMembers.length}</p>
                </div>
                <div className="bg-white p-3 rounded-xl border border-green-100 shadow-2xs">
                  <span className="text-xs text-gray-500">Commodity</span>
                  <p className="text-lg font-bold text-gray-800 truncate">{cropT(aggCrop)}</p>
                </div>
                <div className="bg-white p-3 rounded-xl border border-green-100 shadow-2xs">
                  <span className="text-xs text-gray-500">Est. Realization</span>
                  <p className="text-lg font-bold text-green-700">₹{estLotValue.toLocaleString('en-IN')}</p>
                </div>
              </div>

              {/* Publish Form */}
              <form onSubmit={handleCreateAggregatedLot} className="space-y-3">
                <div>
                  <label className="label text-xs">Asking Price (₹/quintal)</label>
                  <div className="relative">
                    <DollarSign className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="number"
                      value={aggAskingPrice}
                      onChange={(e) => setAggAskingPrice(e.target.value)}
                      required
                      min="100"
                      className="input pl-9 text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="label text-xs">Quality Grade</label>
                    <select
                      value={aggGrade}
                      onChange={(e) => setAggGrade(e.target.value)}
                      className="input text-xs"
                    >
                      <option value="A">Grade A (Premium)</option>
                      <option value="B">Grade B (Standard)</option>
                      <option value="C">Grade C (Commercial)</option>
                    </select>
                  </div>
                  <div>
                    <label className="label text-xs">Consolidation Hub</label>
                    <input
                      type="text"
                      value={aggLocation}
                      onChange={(e) => setAggLocation(e.target.value)}
                      required
                      className="input text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="label text-xs">Lot Description / Quality Notes</label>
                  <textarea
                    rows={2}
                    value={aggNotes}
                    onChange={(e) => setAggNotes(e.target.value)}
                    placeholder="e.g. Graded & dried in certified FPO godown"
                    className="input text-xs"
                  />
                </div>

                {aggError && (
                  <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">{aggError}</p>
                )}

                {createdLotSuccess ? (
                  <div className="p-3 bg-green-100/80 border border-green-300 rounded-xl text-center space-y-2">
                    <p className="text-xs font-bold text-green-800 flex items-center justify-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-green-700" />
                      Bulk Lot {createdLotSuccess.public_id} Created!
                    </p>
                    <div className="flex gap-2 justify-center">
                      <button
                        type="button"
                        onClick={() => {
                          setCreatedLotSuccess(null);
                          setActiveTab('lots');
                        }}
                        className="btn-primary btn-sm text-xs"
                      >
                        View in Lots List
                      </button>
                      <button
                        type="button"
                        onClick={() => setCreatedLotSuccess(null)}
                        className="btn-secondary btn-sm text-xs"
                      >
                        Create Another
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    type="submit"
                    disabled={creatingLot || selectedMembers.length === 0}
                    className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-60 text-sm py-2.5"
                  >
                    <Plus className="w-4 h-4" />
                    {creatingLot ? 'Publishing Lot...' : `Publish Collective Lot (${totalAggregatedQty} qtl)`}
                  </button>
                )}
              </form>

              <div className="mt-3 bg-white/80 rounded-xl p-2.5 text-xs text-gray-600">
                <span className="font-semibold text-green-800">FPO Advantage: </span>
                Aggregating smallholder produce enables wholesale buyers to source bulk volumes in one transaction, saving logistics costs and yielding up to 12% higher farmgate prices.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PUBLISHED LOTS & BUYER OFFERS */}
      {activeTab === 'lots' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">Aggregated Marketplace Listings</h2>
            <button
              onClick={() => setActiveTab('aggregation')}
              className="btn-primary btn-sm flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" />
              <span>Aggregate New Lot</span>
            </button>
          </div>

          {lots.length === 0 ? (
            <div className="card text-center py-12">
              <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-700">No FPO lots published yet</h3>
              <p className="text-gray-400 text-sm mt-1 max-w-md mx-auto">
                Aggregate member produce in the Aggregation Hub to list unified lots on KrishiLink.
              </p>
              <button
                onClick={() => setActiveTab('aggregation')}
                className="btn-primary btn-sm mt-4 inline-flex items-center gap-1.5"
              >
                Go to Aggregation Hub <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {lots.map((lot) => (
                <div key={lot.id} className="card border border-gray-200">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-100">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-gray-100 text-gray-700 rounded">
                          {lot.public_id}
                        </span>
                        <h3 className="text-base font-bold text-gray-900">
                          {lot.quantity} {lot.unit} {cropT(lot.crop)} (Grade {lot.grade})
                        </h3>
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-green-100 text-green-800">
                          {lot.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1 flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-gray-400" />
                        {lot.location || lot.district || 'Nashik'} · Asking Price:{' '}
                        <span className="font-semibold text-green-700">
                          ₹{lot.asking_price ? lot.asking_price.toLocaleString('en-IN') : 'Market Rate'}/qtl
                        </span>
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Link
                        to={`/matches?crop=${lot.crop}&lot_id=${lot.id}`}
                        className="btn-secondary btn-sm flex items-center gap-1 text-xs"
                      >
                        Find Buyers <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>

                  {/* Offers Section for this lot */}
                  <div className="mt-3 pt-2">
                    <p className="text-xs font-semibold text-gray-700 mb-2">
                      Buyer Offers Received ({lot.offers_count}):
                    </p>
                    {lot.offers && lot.offers.length > 0 ? (
                      <div className="space-y-2">
                        {lot.offers.map((offer) => (
                          <div
                            key={offer.id}
                            className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-gray-50 rounded-xl text-xs gap-2 border border-gray-100"
                          >
                            <div>
                              <span className="font-bold text-gray-900 text-sm">
                                ₹{offer.offered_price.toLocaleString('en-IN')} / qtl
                              </span>{' '}
                              <span className="text-gray-500">for {offer.quantity} quintals</span>
                              {offer.notes && <p className="text-gray-400 mt-0.5 italic">{offer.notes}</p>}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-medium">
                                {offer.status}
                              </span>
                              <Link to="/offers" className="btn-primary btn-sm text-xs py-1 px-2.5">
                                Review Offer
                              </Link>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">No incoming purchase offers yet for this lot.</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: MEMBER FARMERS ROSTER */}
      {activeTab === 'members' && (
        <div className="card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-gray-900">FPO Member Registry</h2>
              <p className="text-gray-500 text-xs mt-0.5">
                Manage registered farmers, their farm acreage, and harvest availability.
              </p>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by name, crop, village..."
                  value={searchMember}
                  onChange={(e) => setSearchMember(e.target.value)}
                  className="input pl-9 text-xs py-1.5 w-60"
                />
              </div>
              <button
                onClick={() => setShowAddMemberModal(true)}
                className="btn-primary btn-sm flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Add Member</span>
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                <tr>
                  <th className="py-3 px-3">Farmer Name</th>
                  <th className="py-3 px-3">Contact</th>
                  <th className="py-3 px-3">Village / District</th>
                  <th className="py-3 px-3">Land Size</th>
                  <th className="py-3 px-3">Primary Crop</th>
                  <th className="py-3 px-3">Ready Quantity</th>
                  <th className="py-3 px-3">Grade</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredMembers.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-gray-400">
                      No members match your search query.
                    </td>
                  </tr>
                ) : (
                  filteredMembers.map((m) => (
                    <tr key={m.id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="py-3 px-3 font-semibold text-gray-900">{m.farmer_name}</td>
                      <td className="py-3 px-3 text-gray-600 flex items-center gap-1 mt-1">
                        <Phone className="w-3 h-3 text-gray-400" />
                        {m.phone || '—'}
                      </td>
                      <td className="py-3 px-3 text-gray-600">
                        {m.village ? `${m.village}, ` : ''}{m.district || 'Nashik'}
                      </td>
                      <td className="py-3 px-3 text-gray-600">{m.land_acres} acres</td>
                      <td className="py-3 px-3 font-medium text-gray-800">{cropT(m.primary_crop)}</td>
                      <td className="py-3 px-3 font-bold text-green-700">{m.ready_quantity_qtl} qtl</td>
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded font-semibold text-[10px]">
                          Grade {m.grade}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* QUICK LINKS SECTION */}
      <div className="grid sm:grid-cols-3 gap-4">
        <Link to="/prices" className="card-hover flex items-center gap-3 group">
          <TrendingUp className="w-8 h-8 text-green-600" />
          <div>
            <p className="font-semibold text-gray-800">{t('marketPrices') || 'Market Prices'}</p>
            <p className="text-xs text-gray-500">Live Agmarknet Mandi Rates</p>
          </div>
        </Link>
        <Link to="/offers" className="card-hover flex items-center gap-3 group">
          <Package className="w-8 h-8 text-blue-600" />
          <div>
            <p className="font-semibold text-gray-800">{t('offers') || 'Offers'}</p>
            <p className="text-xs text-gray-500">Manage Buyer Negotiations</p>
          </div>
        </Link>
        <Link to="/map" className="card-hover flex items-center gap-3 group">
          <MapPin className="w-8 h-8 text-purple-600" />
          <div>
            <p className="font-semibold text-gray-800">{t('map') || 'Market Map'}</p>
            <p className="text-xs text-gray-500">Discover Nearby Buyers & Storage</p>
          </div>
        </Link>
      </div>

      {/* MODAL: ADD MEMBER */}
      {showAddMemberModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl relative animate-in fade-in zoom-in duration-150">
            <button
              onClick={() => setShowAddMemberModal(false)}
              className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-bold text-gray-900 mb-1">Onboard Member Farmer</h3>
            <p className="text-xs text-gray-500 mb-4">
              Register a member farmer to participate in collective bargaining and produce aggregation.
            </p>

            <form onSubmit={handleAddMemberSubmit} className="space-y-3">
              <div>
                <label className="label text-xs">Farmer Full Name *</label>
                <input
                  type="text"
                  required
                  value={newMember.farmer_name}
                  onChange={(e) => setNewMember({ ...newMember, farmer_name: e.target.value })}
                  placeholder="e.g. Dnyaneshwar Bhor"
                  className="input text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="label text-xs">Mobile Phone</label>
                  <input
                    type="tel"
                    value={newMember.phone}
                    onChange={(e) => setNewMember({ ...newMember, phone: e.target.value })}
                    placeholder="10-digit number"
                    className="input text-xs"
                  />
                </div>
                <div>
                  <label className="label text-xs">Village / Town</label>
                  <input
                    type="text"
                    value={newMember.village}
                    onChange={(e) => setNewMember({ ...newMember, village: e.target.value })}
                    placeholder="e.g. Niphad"
                    className="input text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="label text-xs">Primary Crop *</label>
                  <select
                    value={newMember.primary_crop}
                    onChange={(e) => setNewMember({ ...newMember, primary_crop: e.target.value })}
                    className="input text-xs"
                  >
                    <option value="Onion">Onion</option>
                    <option value="Tomato">Tomato</option>
                    <option value="Soybean">Soybean</option>
                    <option value="Wheat">Wheat</option>
                    <option value="Cotton">Cotton</option>
                  </select>
                </div>
                <div>
                  <label className="label text-xs">Land Size (Acres)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newMember.land_acres}
                    onChange={(e) => setNewMember({ ...newMember, land_acres: e.target.value })}
                    placeholder="e.g. 5.0"
                    className="input text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="label text-xs">Ready Quantity (Quintals)</label>
                  <input
                    type="number"
                    value={newMember.ready_quantity_qtl}
                    onChange={(e) => setNewMember({ ...newMember, ready_quantity_qtl: e.target.value })}
                    placeholder="e.g. 250"
                    className="input text-xs"
                  />
                </div>
                <div>
                  <label className="label text-xs">Expected Quality</label>
                  <select
                    value={newMember.grade}
                    onChange={(e) => setNewMember({ ...newMember, grade: e.target.value })}
                    className="input text-xs"
                  >
                    <option value="A">Grade A</option>
                    <option value="B">Grade B</option>
                    <option value="C">Grade C</option>
                  </select>
                </div>
              </div>

              {memberActionMsg && (
                <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">{memberActionMsg}</p>
              )}

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddMemberModal(false)}
                  className="btn-secondary flex-1 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addingMember}
                  className="btn-primary flex-1 text-xs flex items-center justify-center gap-1.5"
                >
                  {addingMember ? 'Saving...' : 'Register Farmer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
