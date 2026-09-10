export function Card({ className="", children, ...props }) {
  return <div className={`rounded-xl border bg-white shadow-sm ${className}`} {...props}>{children}</div>;
}
export function CardHeader({ className="", children, ...props }) {
  return <div className={`p-6 pb-2 ${className}`} {...props}>{children}</div>;
}
export function CardTitle({ className="", children, ...props }) {
  return <h3 className={`text-lg font-semibold leading-none tracking-tight ${className}`} {...props}>{children}</h3>;
}
export function CardContent({ className="", children, ...props }) {
  return <div className={`p-6 pt-2 ${className}`} {...props}>{children}</div>;
}
