import { useState, useEffect } from 'react';
import { CheckCircle2, Clock, Package, Truck, Wallet } from 'lucide-react';
import { getTransactions } from '../services/api';
import { StatusBadge } from '../components/Badges';
import { LoadingState, EmptyState } from '../components/States';
import { useLanguage } from '../hooks/useLanguage';

// Stage definitions
const STAGES = [
  { key: 'CREATED',            transKey: 'orderCreated',     label: 'Order Created',       icon: Package },
  { key: 'PAYMENT_PENDING',    transKey: 'escrowInitiated',  label: 'Escrow Initiated',    icon: Clock },
  { key: 'PAYMENT_CONFIRMED',  transKey: 'paymentEscrowed',  label: 'Payment Escrowed',    icon: Wallet },
  { key: 'PROCESSING',         transKey: 'producePrepared',  label: 'Produce Prepared',    icon: Package },
  { key: 'READY_FOR_DISPATCH', transKey: 'readyForDispatch', label: 'Ready for Dispatch',  icon: Truck },
  { key: 'IN_TRANSIT',         transKey: 'inTransit',        label: 'In Transit',          icon: Truck },
  { key: 'DELIVERED',          transKey: 'delivered',        label: 'Delivered',           icon: CheckCircle2 },
  { key: 'COMPLETED',          transKey: 'settledCompleted', label: 'Settled & Completed', icon: CheckCircle2 },
];

function TransactionTimeline({ status, t }) {
  const currentIdx = STAGES.findIndex(s => s.key === status);
  const activeIdx = currentIdx >= 0 ? currentIdx : 0;

  return (
    <div className="flex flex-col gap-0 mt-4">
      {STAGES.map((stage, i) => {
        const done = i <= activeIdx;
        const current = i === activeIdx;
        const Icon = stage.icon;

        return (
          <div key={stage.key} className="flex items-start gap-3">
            {/* Icon + connector line */}
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 flex-shrink-0 ${
                done ? 'bg-green-600 border-green-600 text-white'
                : current ? 'bg-green-100 border-green-600 text-green-600'
                : 'bg-white border-gray-200 text-gray-300'
              }`}>
                <Icon className="w-4 h-4" />
              </div>
              {i < STAGES.length - 1 && (
                <div className={`w-0.5 h-6 mt-1 ${done ? 'bg-green-400' : 'bg-gray-200'}`} />
              )}
            </div>

            {/* Label */}
            <div className="pb-4">
              <p className={`text-sm font-medium leading-relaxed ${
                done ? 'text-gray-900'
                : current ? 'text-green-700 font-semibold'
                : 'text-gray-400'
              }`}>
                {t(stage.transKey) || stage.label}
                {current && (
                  <span className="ml-2 badge-yellow text-xs">Current</span>
                )}
                {done && !current && (
                  <span className="ml-2 text-xs text-green-500 font-bold">✓</span>
                )}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TransactionCard({ txn, t, cropT }) {
  const [showTimeline, setShowTimeline] = useState(false);
  const total = Number(txn.gross_value || txn.total_amount || 0);
  const status = (txn.status || 'CREATED').toUpperCase();
  const stageIdx = STAGES.findIndex(s => s.key === status);
  const progressPct = stageIdx >= 0 ? ((stageIdx + 1) / STAGES.length) * 100 : 15;

  return (
    <div className="card">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="font-mono text-xs text-gray-400">#{String(txn.id).slice(0, 8)}</span>
            <StatusBadge status={status} />
          </div>
          <h3 className="font-bold text-gray-900">{cropT(txn.crop_name || txn.crop) || 'Produce Order'}</h3>
          <p className="text-sm text-gray-500 mt-0.5">Lot #{String(txn.lot_id || '').slice(0, 8)}</p>
        </div>

        {/* Amount */}
        <div className="text-right">
          <p className="text-2xl font-bold text-green-800">
            ₹{total.toLocaleString('en-IN')}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">
            Gross Escrow Value
          </p>
        </div>
      </div>

      {/* Stage summary */}
      <div className="bg-gray-50 rounded-xl p-3 mb-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-gray-700">
            Current stage: <span className="text-green-700 font-semibold">
              {status.replace(/_/g, ' ')}
            </span>
          </p>
          <span className="text-xs text-gray-500 font-medium">
            {stageIdx >= 0 ? `${stageIdx + 1} of ${STAGES.length}` : 'In progress'}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Timeline toggle */}
      <button
        onClick={() => setShowTimeline(!showTimeline)}
        className="text-green-700 text-sm font-semibold hover:underline"
      >
        {showTimeline ? 'Hide Timeline' : 'Show Full Timeline'}
      </button>

      {showTimeline && (
        <TransactionTimeline status={status} t={t} />
      )}
    </div>
  );
}

export default function TransactionsPage() {
  const { t, cropT } = useLanguage();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const res = await getTransactions();
      if (res && res.success && Array.isArray(res.data)) {
        setTransactions(res.data);
      }
      setLoading(false);
    }
    load();
  }, []);

  const totalAmount = transactions.reduce((s, t) => s + Number(t.gross_value || t.total_amount || 0), 0);
  const completedCount = transactions.filter(t => (t.status || '').toUpperCase() === 'COMPLETED').length;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('transactions') || 'Orders & Transactions'}</h1>
        <p className="text-gray-500 text-sm mt-1">Track escrow transactions and delivery milestones</p>
      </div>

      {/* Summary */}
      {!loading && transactions.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center p-4">
            <p className="text-2xl font-bold text-gray-900">{transactions.length}</p>
            <p className="text-sm text-gray-500 mt-0.5">{t('transactions') || 'Total Orders'}</p>
          </div>
          <div className="card text-center p-4">
            <p className="text-2xl font-bold text-green-700">{completedCount}</p>
            <p className="text-sm text-gray-500 mt-0.5">{t('completed') || 'Completed'}</p>
          </div>
          <div className="card text-center p-4">
            <p className="text-lg font-bold text-gray-900">₹{(totalAmount / 100000).toFixed(1)}L</p>
            <p className="text-sm text-gray-500 mt-0.5">{t('totalValue') || 'Total Value'}</p>
          </div>
        </div>
      )}

      {loading ? <LoadingState /> : transactions.length === 0 ? (
        <EmptyState
          title="No transactions yet"
          description="Accept a buyer offer to begin an escrow order transaction."
        />
      ) : (
        <div className="space-y-4">
          {transactions.map(txn => (
            <TransactionCard key={txn.id} txn={txn} t={t} cropT={cropT} />
          ))}
        </div>
      )}
    </div>
  );
}

