import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getTradeRoom, transitionTrade, addTradeNote } from '../services/api';

export default function TradeRoomPage() {
  const { id } = useParams();

  const [room, setRoom] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);

  // Notes state
  const [newNote, setNewNote] = useState('');
  const [noteLoading, setNoteLoading] = useState(false);

  // Modals state
  const [showDocModal, setShowDocModal] = useState(false);
  const [confirmModal, setConfirmModal] = useState(null); // { targetStatus, title, prompt, defaultReason }
  const [transitionReason, setTransitionReason] = useState('');

  const loadRoom = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    const res = await getTradeRoom(id);
    if (res.success && res.data) {
      setRoom(res.data);
    } else {
      setError(res.error || res.message || 'Failed to load Trade Room');
    }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    loadRoom();
  }, [loadRoom]);

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    setNoteLoading(true);
    setActionError(null);
    const res = await addTradeNote(id, newNote.trim());
    if (res.success) {
      setNewNote('');
      await loadRoom();
    } else {
      setActionError(res.error || res.message || 'Failed to add note');
    }
    setNoteLoading(false);
  };

  const handleExecuteTransition = async () => {
    if (!confirmModal) return;
    setActionLoading(true);
    setActionError(null);
    const res = await transitionTrade(id, confirmModal.targetStatus, transitionReason.trim() || undefined);
    if (res.success) {
      setConfirmModal(null);
      setTransitionReason('');
      await loadRoom();
    } else {
      setActionError(res.error || res.message || 'State transition failed');
    }
    setActionLoading(false);
  };

  const getStatusBadgeClass = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'COMPLETED') return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    if (s === 'PAYMENT_CONFIRMED' || s === 'IN_TRANSIT' || s === 'DELIVERED') return 'bg-blue-100 text-blue-800 border-blue-300';
    if (s === 'DISPUTED') return 'bg-rose-100 text-rose-800 border-rose-300';
    if (s === 'CANCELLED') return 'bg-gray-100 text-gray-700 border-gray-300';
    return 'bg-amber-100 text-amber-800 border-amber-300';
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-12 px-4 text-center">
        <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-emerald-600 border-t-transparent mb-4"></div>
        <p className="text-gray-600 font-medium">Loading Unified Trade Room #{id}...</p>
      </div>
    );
  }

  if (error || !room) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center">
          <h2 className="text-xl font-bold text-rose-900 mb-2">Trade Room Unavailable</h2>
          <p className="text-rose-700 mb-6">{error || 'Trade record not found or access unauthorized.'}</p>
          <Link
            to="/transactions"
            className="inline-flex items-center px-4 py-2 bg-rose-600 text-white font-semibold rounded-lg hover:bg-rose-700 transition"
          >
            ← Back to Transactions
          </Link>
        </div>
      </div>
    );
  }

  const { public_id, status, terms, payment, logistics, quality, next_action, timeline, buyer, seller } = room;

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Top Navigation & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <div className="flex items-center gap-3">
            <Link to="/transactions" className="text-sm font-semibold text-emerald-700 hover:underline">
              ← Transactions
            </Link>
            <span className="text-gray-300">|</span>
            <span className="text-xs font-bold tracking-wider px-2.5 py-0.5 rounded-full border bg-gray-50 text-gray-700 border-gray-200 uppercase">
              Unified Trade Room
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-gray-900 mt-1 flex items-center gap-3 flex-wrap">
            <span>Trade #{public_id}</span>
            <span className={`text-xs font-bold px-3 py-1 rounded-full border ${getStatusBadgeClass(status)}`}>
              {status}
            </span>
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Agreed Commodity: <span className="font-semibold text-gray-800">{terms?.crop_name || 'Produce'}</span> •{' '}
            {terms?.quantity} {terms?.unit} (Grade {terms?.grade})
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowDocModal(true)}
            className="px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-semibold rounded-lg shadow-sm transition flex items-center gap-2"
          >
            📄 View Trade Document
          </button>
        </div>
      </div>

      {actionError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-lg text-sm flex justify-between items-center">
          <span>{actionError}</span>
          <button onClick={() => setActionError(null)} className="font-bold ml-4">✕</button>
        </div>
      )}

      {/* 1. Next Action Banner */}
      <div className={`p-5 rounded-xl border ${next_action.action_required ? 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200 shadow-sm' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${next_action.action_required ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`}></span>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-900">
                {next_action.action_required ? `Required Action (${next_action.responsible_role.toUpperCase()})` : 'Lifecycle Status'}
              </span>
            </div>
            <h2 className="text-lg font-bold text-gray-900 mt-1">{next_action.action_title}</h2>
            <p className="text-sm text-gray-600 max-w-2xl mt-0.5">{next_action.action_description}</p>
          </div>

          {next_action.is_current_user_action && (
            <div className="flex items-center gap-2">
              {next_action.action_type === 'CONFIRM_PAYMENT' && (
                <button
                  onClick={() => setConfirmModal({
                    targetStatus: 'PAYMENT_CONFIRMED',
                    title: 'Authorize Sandbox Payment',
                    prompt: 'Confirm simulated payment lock of Rs. ' + (payment?.gross_value || 0).toLocaleString() + '. Funds are locked in sandbox environment.',
                    defaultReason: 'Sandbox payment authorized by buyer.'
                  })}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-lg shadow transition"
                >
                  💳 Authorize Sandbox Payment
                </button>
              )}

              {next_action.action_type === 'PREPARE_DISPATCH' && (
                <button
                  onClick={() => setConfirmModal({
                    targetStatus: 'READY_FOR_DISPATCH',
                    title: 'Confirm Produce Ready for Dispatch',
                    prompt: 'Confirm that produce is aggregated, graded, and packaged for transport.',
                    defaultReason: 'Produce packed and ready for dispatch.'
                  })}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-lg shadow transition"
                >
                  📦 Mark Ready for Dispatch
                </button>
              )}

              {next_action.action_type === 'DISPATCH' && (
                <button
                  onClick={() => setConfirmModal({
                    targetStatus: 'IN_TRANSIT',
                    title: 'Mark as Dispatched / In Transit',
                    prompt: 'Confirm that goods have departed pickup location towards buyer destination.',
                    defaultReason: 'Dispatched via self-arranged carrier.'
                  })}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-lg shadow transition"
                >
                  🚚 Mark as Dispatched
                </button>
              )}

              {next_action.action_type === 'CONFIRM_DELIVERY' && (
                <button
                  onClick={() => setConfirmModal({
                    targetStatus: 'DELIVERED',
                    title: 'Confirm Delivery Arrival',
                    prompt: 'Confirm physical arrival of goods at destination facility.',
                    defaultReason: 'Shipment received at buyer facility.'
                  })}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-lg shadow transition"
                >
                  📍 Confirm Delivery Arrival
                </button>
              )}

              {next_action.action_type === 'FINALIZE_ACCEPTANCE' && (
                <button
                  onClick={() => setConfirmModal({
                    targetStatus: 'COMPLETED',
                    title: 'Accept Produce & Finalize Settlement',
                    prompt: 'Confirm final quantity and quality acceptance to complete trade and release payment.',
                    defaultReason: 'Produce accepted in good order. Trade settled.'
                  })}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-lg shadow transition"
                >
                  ✅ Accept & Complete Trade
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Grid: Commercial Terms & Fulfilment Pillars */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Commercial Terms, Payment, Logistics, Quality */}
        <div className="lg:col-span-2 space-y-6">
          {/* Card 1: Agreed Commercial Terms */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-gray-900 border-b border-gray-100 pb-3 mb-4 flex items-center justify-between">
              <span>📋 Agreed Commercial Terms</span>
              <span className="text-xs font-normal text-gray-500">Immutable Snapshot</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-500">Agreed Price</p>
                <p className="text-base font-bold text-gray-900 mt-0.5">
                  ₹{terms?.price_per_unit?.toLocaleString()} / {terms?.unit}
                </p>
              </div>

              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-500">Committed Quantity</p>
                <p className="text-base font-bold text-gray-900 mt-0.5">
                  {terms?.quantity} {terms?.unit}
                </p>
              </div>

              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-500">Gross Contract Value</p>
                <p className="text-base font-bold text-emerald-700 mt-0.5">
                  ₹{terms?.gross_value?.toLocaleString()}
                </p>
              </div>

              <div className="sm:col-span-2 bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-500">Pickup Location</p>
                <p className="text-sm font-semibold text-gray-800 mt-0.5">{terms?.pickup_location || 'Not specified'}</p>
              </div>

              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-500">Delivery Window</p>
                <p className="text-sm font-semibold text-gray-800 mt-0.5">{terms?.delivery_window || 'Standard 3-5 days'}</p>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
              <span>Buyer: <strong className="text-gray-800">{buyer?.full_name}</strong> ({buyer?.location || 'Mumbai'})</span>
              <span>Seller: <strong className="text-gray-800">{seller?.full_name}</strong> ({seller?.location || 'Nashik'})</span>
            </div>
          </div>

          {/* Card 2: Money & Payment Status */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-bold text-gray-900 border-b border-gray-100 pb-3 mb-4 flex items-center justify-between">
              <span>💳 Settlement & Payment Breakdown</span>
              <span className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded">
                {payment?.status}
              </span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-4">
              <div>
                <p className="text-xs text-gray-500">Gross Value</p>
                <p className="text-sm font-bold text-gray-900 mt-0.5">₹{payment?.gross_value?.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Transport Est.</p>
                <p className="text-sm font-semibold text-gray-700 mt-0.5">₹{payment?.transport_cost?.toLocaleString() || '0'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Platform Fee</p>
                <p className="text-sm font-semibold text-gray-700 mt-0.5">₹{payment?.platform_fee?.toLocaleString() || '0'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Est. Farmer Net</p>
                <p className="text-sm font-bold text-emerald-700 mt-0.5">₹{payment?.net_realization?.toLocaleString()}</p>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800 flex items-start gap-2">
              <span className="text-sm">ℹ️</span>
              <span><strong>Sandbox Payment Environment:</strong> {payment?.note}</span>
            </div>
          </div>

          {/* Card 3: Logistics & Quality Pillars */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Logistics Pillar */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center justify-between">
                <span>🚚 Logistics & Transit</span>
                <span className="text-xs font-medium text-gray-500">{logistics?.status}</span>
              </h4>
              <p className="text-xs text-gray-600 mb-2">
                <strong>Carrier:</strong> {logistics?.carrier_status}
              </p>
              <div className="text-xs text-gray-500 space-y-1 bg-gray-50 p-2.5 rounded border border-gray-100">
                <p><strong>Origin:</strong> {logistics?.origin || 'Seller Facility'}</p>
                <p><strong>Destination:</strong> {logistics?.destination || 'Buyer Facility'}</p>
              </div>
              <p className="text-[11px] text-gray-400 mt-3 italic">{logistics?.note}</p>
            </div>

            {/* Quality Pillar */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center justify-between">
                <span>🧪 Quality Specification</span>
                <span className="text-xs font-bold px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded">
                  Grade {quality?.agreed_grade}
                </span>
              </h4>
              <p className="text-xs text-gray-600 mb-2">
                <strong>Verification:</strong> {quality?.verification_status}
              </p>
              <div className="text-xs text-gray-600 bg-gray-50 p-2.5 rounded border border-gray-100">
                <p><strong>Agreed Grade:</strong> Grade {quality?.agreed_grade}</p>
                <p className="text-gray-500 text-[11px] mt-1">{quality?.note}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right 1 Column: Chronological Audit Timeline & Communication */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-base font-bold text-gray-900 border-b border-gray-100 pb-3 mb-4">
              ⏱️ Trade Event History
            </h3>

            {/* Timeline Stream */}
            <div className="relative border-l-2 border-emerald-100 ml-3 space-y-6 my-2">
              {timeline && timeline.map((ev, idx) => (
                <div key={ev.id || idx} className="relative pl-5">
                  <span className={`absolute -left-1.5 top-1.5 w-3 h-3 rounded-full border-2 border-white ${ev.event_type === 'USER_NOTE' ? 'bg-blue-500' : 'bg-emerald-600'}`}></span>
                  <div className="text-xs font-bold text-gray-900 flex items-center justify-between">
                    <span>{ev.title}</span>
                    <span className="text-[10px] font-normal text-gray-400">
                      {new Date(ev.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  {ev.description && (
                    <p className="text-xs text-gray-600 mt-1 bg-gray-50 p-2 rounded border border-gray-100">
                      {ev.description}
                    </p>
                  )}
                  <p className="text-[10px] text-gray-400 mt-0.5">
                    Actor: {ev.actor_role ? ev.actor_role.toUpperCase() : 'SYSTEM'} • {new Date(ev.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>

            {/* Add User Note Form */}
            <form onSubmit={handleAddNote} className="mt-6 pt-4 border-t border-gray-100">
              <label className="block text-xs font-bold text-gray-700 mb-1">
                Add Trade Note
              </label>
              <textarea
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Record operational note, packaging note, or update..."
                className="w-full text-xs p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                rows="2"
                maxLength={1000}
                required
              />
              <div className="flex justify-end mt-2">
                <button
                  type="submit"
                  disabled={noteLoading || !newNote.trim()}
                  className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white text-xs font-semibold rounded shadow-sm transition"
                >
                  {noteLoading ? 'Saving...' : 'Post Note'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Modal: State Transition Confirmation */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-gray-900">{confirmModal.title}</h3>
            <p className="text-sm text-gray-600">{confirmModal.prompt}</p>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Reason / Operational Notes (Optional)
              </label>
              <input
                type="text"
                value={transitionReason}
                onChange={(e) => setTransitionReason(e.target.value)}
                placeholder={confirmModal.defaultReason}
                className="w-full text-xs p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setConfirmModal(null)}
                disabled={actionLoading}
                className="px-4 py-2 border border-gray-300 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteTransition}
                disabled={actionLoading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow transition"
              >
                {actionLoading ? 'Updating...' : 'Confirm Action'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Demo Document Viewer */}
      {showDocModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full p-8 shadow-2xl relative space-y-6 max-h-[90vh] overflow-y-auto">
            {/* Watermark Notice */}
            <div className="bg-amber-100 border border-amber-300 text-amber-900 font-black text-center py-2 text-xs uppercase tracking-widest rounded-lg">
              DEMO DOCUMENT — NOT A LEGAL CONTRACT
            </div>

            <div className="border border-gray-300 p-6 rounded-lg font-mono text-xs space-y-4 bg-gray-50">
              <div className="text-center pb-3 border-b border-gray-300">
                <h2 className="text-base font-bold text-gray-900">KRISHILINK AGRICULTURAL TRADE SLIP</h2>
                <p className="text-gray-500">Trade Reference: {public_id}</p>
                <p className="text-gray-400 text-[10px]">Date: {new Date(room.created_at).toLocaleString()}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="font-bold text-gray-700">BUYER:</p>
                  <p>{buyer?.full_name}</p>
                  <p>{buyer?.location || 'Mumbai'}</p>
                </div>
                <div>
                  <p className="font-bold text-gray-700">SELLER / PRODUCER:</p>
                  <p>{seller?.full_name}</p>
                  <p>{seller?.location || 'Nashik'}</p>
                </div>
              </div>

              <div className="pt-2 border-t border-gray-300">
                <p className="font-bold text-gray-700 mb-1">COMMODITY DETAILS:</p>
                <p>Crop: {terms?.crop_name} (Grade {terms?.grade})</p>
                <p>Quantity: {terms?.quantity} {terms?.unit}</p>
                <p>Unit Price: Rs. {terms?.price_per_unit?.toLocaleString()} / {terms?.unit}</p>
                <p className="font-bold text-emerald-800 mt-1">Total Contract Value: Rs. {terms?.gross_value?.toLocaleString()}</p>
              </div>

              <div className="pt-2 border-t border-gray-300">
                <p className="font-bold text-gray-700 mb-1">FULFILLMENT & ESCROW STATUS:</p>
                <p>Status: {status}</p>
                <p>Payment: {payment?.status} (Sandbox Environment)</p>
                <p>Pickup: {terms?.pickup_location}</p>
                <p>Delivery: {terms?.delivery_location}</p>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowDocModal(false)}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-900 text-white text-xs font-bold rounded-lg shadow"
              >
                Close Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
