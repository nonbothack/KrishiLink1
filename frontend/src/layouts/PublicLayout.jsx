import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
export default function PublicLayout({children}) {return <div className="public-shell"><Navbar/><main id="main" tabIndex={-1}>{children || <Outlet/>}</main><Footer/></div>;}
