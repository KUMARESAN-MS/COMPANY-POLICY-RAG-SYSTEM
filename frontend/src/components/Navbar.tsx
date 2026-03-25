import { Link, useLocation } from 'react-router-dom';
import { ShieldCheck, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="glass-nav px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-10 h-10 premium-gradient rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
          <ShieldCheck className="text-white w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-glow">PolicyGuard</h1>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest leading-none">Intelligence Engine</p>
        </div>
      </div>

      <div className="flex items-center gap-8 bg-white/5 px-6 py-2 rounded-full border border-white/5">
        <Link 
          to="/" 
          className={cn(
            "text-sm font-medium transition-colors hover:text-primary",
            location.pathname === '/' ? "text-primary" : "text-muted-foreground"
          )}
        >
          Ask Policy
        </Link>
        <Link 
          to="/admin" 
          className={cn(
            "text-sm font-medium transition-colors hover:text-primary",
            location.pathname === '/admin' ? "text-primary" : "text-muted-foreground"
          )}
        >
          Admin Dashboard
        </Link>
      </div>

      <div className="flex items-center gap-3">
        <a 
          href="https://github.com" 
          target="_blank" 
          rel="noreferrer"
          className="p-2 hover:bg-white/5 rounded-full transition-colors"
        >
          <Globe className="w-5 h-5 text-muted-foreground" />
        </a>
      </div>
    </nav>
  );
}
