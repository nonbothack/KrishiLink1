import React from 'react';

/**
 * Mobile-first sticky bottom action bar ensuring single primary action is always thumb-accessible.
 */
export function MobileBottomAction({
  children,
  className = '',
}) {
  return (
    <div
      className={`fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-gray-200 p-3 sm:hidden shadow-lg ${className}`}
    >
      <div className="max-w-md mx-auto flex items-center justify-between gap-3">
        {children}
      </div>
    </div>
  );
}

export default MobileBottomAction;
