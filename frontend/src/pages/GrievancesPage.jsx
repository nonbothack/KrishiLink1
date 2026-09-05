// =============================================================
// Grievances & Customer Support Page
// File and track support tickets & transaction disputes
// =============================================================

import { useState, useEffect } from 'react';
import { AlertTriangle, Plus, Clock, CheckCircle2, MessageSquare, ShieldAlert } from 'lucide-react';
import { getGrievances, createGrievance } from '../services/api';
import { LoadingState } from '../components/States';
import { useLanguage } from '../hooks/useLanguage';

const CATEGORIES = [
  { key: 'Price Dispute', labelKey: 'priceDispute' },
  { key: 'Quality Dispute', labelKey: 'qualityDispute' },
  { key: 'Payment Delay', labelKey: 'paymentDelay' },
  { key: 'Delivery & Transport', labelKey: 'deliveryTransport' },
  { key: 'Listing Accuracy', labelKey: 'listingAccuracy' },
  { key: 'Account & Profile', labelKey: 'accountProfile' },
  { key: 'General Inquiry', labelKey: 'generalInquiry' },
];

export default function GrievancesPage() {
  const { t } = useLanguage();
  const [grievances, setGrievances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    transaction_id: '',
    category: 'Price Dispute',
    reason: '',
    description: '',
    priority: 'MEDIUM'
  });
  const [submitting, setSubmitting] = useState(false);
  const [submittedMessage, setSubmittedMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const loadGrievances = async () => {
    setLoading(true);
    setErrorMessage(null);
    const res = await getGrievances();
    if (res && res.success && Array.isArray(res.data)) {
      setGrievances(res.data);
    } else if (res && !res.success) {
      setErrorMessage(res.error || 'Failed to load support tickets. Please refresh.');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadGrievances();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!formData.reason || !formData.description) return;
    setSubmitting(true);
    setErrorMessage(null);

    const payload = {
      category: formData.category,
      reason: formData.reason,
      description: formData.description,
      priority: formData.priority,
      transaction_id: formData.transaction_id || null,
    };

    const res = await createGrievance(payload);
    if (res && res.success) {
      const createdItem = res.data || {
        id: `tkt-${Date.now()}`,
        ticket_number: `KL-TKT-${Date.now().toString().slice(-6)}`,
        reason: `[${formData.category}] ${formData.reason}`,
        description: formData.description,
        status: 'OPEN',
        created_at: new Date().toISOString()
      };
      setGrievances(prev => [createdItem, ...prev]);
      setShowForm(false);
      setFormData({ transaction_id: '', category: 'Price Dispute', reason: '', description: '', priority: 'MEDIUM' });
      setSubmittedMessage('Your ticket has been submitted. Support will investigate and update you within 24 hours.');
      setTimeout(() => setSubmittedMessage(null), 8000);
    } else {
      setErrorMessage(res?.error || 'Could not submit support ticket. Please check fields and retry.');
    }
    setSubmitting(false);
  }

  const getStatusBadge = (status = 'OPEN') => {
    const s = status.toUpperCase();
    if (s === 'OPEN') return 'bg-amber-100 text-amber-800 border border-amber-200';
    if (s === 'UNDER_REVIEW' || s === 'IN_PROGRESS') return 'bg-blue-100 text-blue-800 border border-blue-200';
    if (s === 'RESOLVED' || s === 'CLOSED') return 'bg-green-100 text-green-800 border border-green-200';
    if (s === 'REJECTED') return 'bg-red-100 text-red-800 border border-red-200';
    return 'bg-gray-100 text-gray-700';
  };

  const getStatusLabel = (status = 'OPEN') => {
    const s = status.toUpperCase();
    if (s === 'OPEN') return t('open');
    if (s === 'UNDER_REVIEW' || s === 'IN_PROGRESS') return t('underReview');
    if (s === 'RESOLVED' || s === 'CLOSED') return t('resolved');
    if (s === 'REJECTED') return t('rejected');
    return status;
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('supportGrievances')}</h1>
          <p className="text-gray-500 text-sm mt-1">{t('grievanceSubtitle')}</p>
        </div>
        <button
          onClick={() => { setShowForm(!showForm); setErrorMessage(null); }}
          className="btn-primary flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          {showForm ? t('closeForm') : t('newTicket')}
        </button>
      </div>

      {/* Success alert */}
      {submittedMessage && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3.5 rounded-xl text-sm flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
          <span>{submittedMessage}</span>
        </div>
      )}

      {/* Error alert */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3.5 rounded-xl text-sm flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Ticket creation form */}
      {showForm && (
        <div className="card border-2 border-green-200 shadow-md">
          <h2 className="font-bold text-gray-900 mb-4 flex items-center gap-2 text-lg">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            {t('fileTicketTitle')}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="label">{t('category')} *</label>
                <select
                  className="input"
                  value={formData.category}
                  onChange={(e) => setFormData(p => ({ ...p, category: e.target.value }))}
                  required
                >
                  {CATEGORIES.map(c => <option key={c.key} value={c.key}>{t(c.labelKey)}</option>)}
                </select>
              </div>
              <div>
                <label className="label">{t('priority')}</label>
                <select
                  className="input"
                  value={formData.priority}
                  onChange={(e) => setFormData(p => ({ ...p, priority: e.target.value }))}
                >
                  <option value="LOW">{t('lowPriority')}</option>
                  <option value="MEDIUM">{t('mediumPriority')}</option>
                  <option value="HIGH">{t('highPriority')}</option>
                  <option value="URGENT">{t('urgentPriority')}</option>
                </select>
              </div>
            </div>

            <div>
              <label className="label">{t('subjectSummary')} *</label>
              <input
                className="input"
                placeholder="Brief summary of the issue (e.g. Quality did not match Grade A specification)"
                value={formData.reason}
                onChange={(e) => setFormData(p => ({ ...p, reason: e.target.value }))}
                required
                minLength={3}
                maxLength={150}
              />
            </div>

            <div>
              <label className="label">{t('orderIdOptional')}</label>
              <input
                className="input"
                placeholder="e.g. 5e179e22-046c-49f5 — leave empty if not related to an order"
                value={formData.transaction_id}
                onChange={(e) => setFormData(p => ({ ...p, transaction_id: e.target.value }))}
              />
            </div>

            <div>
              <label className="label">{t('detailedDescription')} *</label>
              <textarea
                className="input resize-none"
                rows={4}
                placeholder="Provide specific details including weights, timestamps, and communications so our operations team can resolve promptly."
                value={formData.description}
                onChange={(e) => setFormData(p => ({ ...p, description: e.target.value }))}
                required
                minLength={10}
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={submitting} className="btn-primary disabled:opacity-60">
                {submitting ? t('submitting') : t('submitTicket')}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                {t('cancel')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tickets List */}
      {loading ? <LoadingState message={t('loading')} /> : (
        <div className="space-y-4">
          {grievances.length === 0 ? (
            <div className="card text-center py-12">
              <MessageSquare className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-700 font-semibold">{t('noActiveTickets')}</p>
              <p className="text-sm text-gray-400 mt-1">{t('noTicketsDesc')}</p>
            </div>
          ) : (
            grievances.map(g => (
              <div key={g.id} className="card hover:border-gray-300 transition-all">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${getStatusBadge(g.status)}`}>
                        {getStatusLabel(g.status)}
                      </span>
                      {g.ticket_number && (
                        <span className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-medium">
                          {g.ticket_number}
                        </span>
                      )}
                      {g.transaction_id && (
                        <span className="text-xs text-gray-400 font-mono">
                          Order: #{g.transaction_id.slice(0, 8)}
                        </span>
                      )}
                    </div>
                    <h3 className="font-bold text-gray-900 text-base mt-1">{g.reason}</h3>
                    <p className="text-gray-700 text-sm mt-1.5 leading-relaxed">{g.description}</p>
                    
                    {g.resolution && (
                      <div className="mt-3 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
                        <p className="text-xs font-bold text-green-800 mb-0.5">{t('officialResolution')}</p>
                        <p className="text-sm text-green-900">{g.resolution}</p>
                      </div>
                    )}
                    
                    <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-3">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{t('filedOn')} {g.created_at ? new Date(g.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }) : 'recently'}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
