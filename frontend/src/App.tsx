import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import AskPage from './pages/AskPage';
import AdminPage from './pages/AdminPage';
import { Toaster } from '@/components/ui/sonner';

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<AskPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
      <Toaster />
    </div>
  );
}

export default App;
