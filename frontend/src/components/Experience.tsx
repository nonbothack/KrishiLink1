import {
  Fragment,
  createElement,
  useCallback,
  useEffect,
  useId,
  useState,
  type ButtonHTMLAttributes,
  type CSSProperties,
  type DependencyList,
  type ElementType,
  type HTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from 'react';
import { AlertCircle, PackageOpen, RefreshCw } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type ButtonSize = 'small' | 'medium' | 'large';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
  iconOnly?: boolean;
}

export function Button({
  children,
  className = '',
  variant = 'primary',
  size = 'medium',
  loading = false,
  fullWidth = false,
  iconOnly = false,
  type = 'button',
  disabled,
  ...props
}: ButtonProps) {
  if (iconOnly && !props['aria-label'] && !props['aria-labelledby']) {
    throw new Error('Icon-only buttons need an accessible name.');
  }

  const variantClass = {
    primary: '',
    secondary: 'secondary',
    danger: 'button-danger',
    ghost: 'button-ghost',
  }[variant];
  const sizeClass = {
    small: 'small',
    medium: '',
    large: 'button-large',
  }[size];
  const classes = [
    'button',
    variantClass,
    sizeClass,
    fullWidth && 'button-full',
    iconOnly && 'button-icon-only',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      {...props}
      type={type}
      className={classes}
      aria-busy={loading || undefined}
      disabled={loading || disabled}
    >
      {loading && <span className="button-spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

type CardProps = HTMLAttributes<HTMLElement> & {
  as?: ElementType;
  variant?: 'default' | 'compact' | 'emphasized';
};

export function Card({ as = 'div', variant = 'default', className = '', ...props }: CardProps) {
  return createElement(as, {
    ...props,
    className: ['card', `card-${variant}`, className].filter(Boolean).join(' '),
  } as never);
}

type Tone = 'success' | 'danger' | 'warning' | 'info' | 'neutral';

type BadgeProps = HTMLAttributes<HTMLSpanElement> & { tone?: Tone };

export function Badge({ children, tone = 'neutral', className = '', ...props }: BadgeProps) {
  return (
    <span {...props} className={['badge', `badge-${tone}`, className].filter(Boolean).join(' ')}>
      {children}
    </span>
  );
}

type StatusPillProps = HTMLAttributes<HTMLSpanElement> & { tone?: Tone };

export function StatusPill({
  children,
  tone = 'neutral',
  className = '',
  ...props
}: StatusPillProps) {
  return (
    <span
      {...props}
      className={['status-pill', `status-pill-${tone}`, className].filter(Boolean).join(' ')}
    >
      {children}
    </span>
  );
}

export function Skeleton({ className = '', ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      {...props}
      aria-hidden="true"
      className={['skeleton', className].filter(Boolean).join(' ')}
    />
  );
}

type FieldElementProps =
  | InputHTMLAttributes<HTMLInputElement>
  | SelectHTMLAttributes<HTMLSelectElement>
  | TextareaHTMLAttributes<HTMLTextAreaElement>;

export interface FieldProps extends Omit<FieldElementProps, 'children' | 'id' | 'className'> {
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  as?: 'input' | 'select' | 'textarea';
  children?: ReactNode;
  id?: string;
  className?: string;
}

export function Field({
  label,
  hint,
  error,
  as = 'input',
  children,
  id: suppliedId,
  className = '',
  'aria-describedby': suppliedDescriptionId,
  ...props
}: FieldProps) {
  const generatedId = useId();
  const id = suppliedId || generatedId;
  const descriptionId =
    [suppliedDescriptionId, hint || error ? `${id}-description` : undefined]
      .filter(Boolean)
      .join(' ') || undefined;
  const fieldProps = {
    ...props,
    id,
    className,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': descriptionId,
  } as FieldElementProps & { id: string; className: string; style?: CSSProperties };

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {createElement(as as ElementType, fieldProps as never, children)}
      {(hint || error) && (
        <p id={`${id}-description`} className={error ? 'field-error' : 'field-hint'}>
          {error || hint}
        </p>
      )}
    </div>
  );
}

type NoticeProps = HTMLAttributes<HTMLDivElement> & { error?: boolean; children: ReactNode };

export function Notice({ children, error = false, className = '', ...props }: NoticeProps) {
  return (
    <div
      {...props}
      className={['notice', error && 'notice-error', className].filter(Boolean).join(' ')}
      role={error ? 'alert' : 'status'}
    >
      <AlertCircle size={20} aria-hidden="true" />
      <div>{children}</div>
    </div>
  );
}

export interface DataStateProps {
  loading?: boolean;
  error?: string | null;
  empty?: ReactNode | boolean;
  onRetry?: () => void;
  staleMessage?: ReactNode;
  offlineMessage?: ReactNode;
  children?: ReactNode;
}

export function DataState({
  loading = false,
  error,
  empty,
  onRetry,
  staleMessage,
  offlineMessage,
  children,
}: DataStateProps) {
  const { t } = useLanguage() as { t: (key: string, fallback?: string) => string };

  if (loading) {
    return (
      <div className="data-state" role="status" aria-live="polite">
        <RefreshCw className="loading-icon" size={24} aria-hidden="true" />
        <p>{t('loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="data-state" role="alert">
        <AlertCircle size={28} aria-hidden="true" />
        <p>{t(error)}</p>
        {onRetry && (
          <button className="button secondary" type="button" onClick={onRetry}>
            {t('retry')}
          </button>
        )}
      </div>
    );
  }

  if (empty) {
    return (
      <div className="data-state" role="status">
        <PackageOpen size={32} aria-hidden="true" />
        <p>{typeof empty === 'string' ? empty : t('empty')}</p>
      </div>
    );
  }

  return (
    <Fragment>
      {offlineMessage && <Notice className="data-state-notice">{offlineMessage}</Notice>}
      {staleMessage && <Notice className="data-state-notice">{staleMessage}</Notice>}
      {children}
    </Fragment>
  );
}

type ResourceResult<TData> = {
  success?: boolean;
  data?: TData;
  error?: string;
  [key: string]: unknown;
};

export type ResourceState<TData> = {
  loading: boolean;
  error: string | null;
  data: TData;
  total?: number;
  retry: () => void;
  [key: string]: unknown;
};

export function useResource<TData = unknown>(
  loader: () => Promise<ResourceResult<TData>>,
  dependencies: DependencyList = [],
  initial?: Partial<ResourceState<TData | []>> | null,
): ResourceState<TData | []> {
  const [revision, setRevision] = useState(0);
  const [resource, setResource] = useState<ResourceState<TData | []>>(() => ({
    loading: initial ? false : true,
    error: null,
    data: [],
    total: 0,
    ...initial,
    retry: () => undefined,
  }));

  useEffect(() => {
    let active = true;
    setResource((previous) => ({ ...previous, loading: true, error: null }));

    Promise.resolve()
      .then(loader)
      .then((result) => {
        if (active) {
          setResource({
            ...result,
            loading: false,
            error: result.success ? null : result.error || 'server',
            data: result.data ?? [],
            retry,
          });
        }
      })
      .catch(() => {
        if (active)
          setResource((previous) => ({ ...previous, loading: false, error: 'network', retry }));
      });

    return () => {
      active = false;
    };
    // Dependencies are supplied explicitly by the calling resource.
  }, [...dependencies, revision]);

  const retry = useCallback(() => setRevision((current) => current + 1), []);
  return { ...resource, retry };
}

export interface PageHeadingProps {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
}

export function PageHeading({ eyebrow, title, description, action }: PageHeadingProps) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
