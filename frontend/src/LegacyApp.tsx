import AppRoutes from './routes/AppRoutes';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
export default function LegacyApp() { return <><AppRoutes /><ToastContainer position="top-right" autoClose={5000} hideProgressBar /></>; }
