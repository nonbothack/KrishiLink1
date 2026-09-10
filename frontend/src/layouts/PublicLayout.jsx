// =============================================================
// Public Layout
// Used by: Landing page, Login, Register, Prices, Map
// Shows: Navbar + Demo Banner + Page content + Footer
// =============================================================

import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function PublicLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#FAFAF7] flex flex-col">
      <Navbar />
      <main className="flex-1">
        {children || <Outlet />}
      </main>
      <Footer />
    </div>
  );
}
