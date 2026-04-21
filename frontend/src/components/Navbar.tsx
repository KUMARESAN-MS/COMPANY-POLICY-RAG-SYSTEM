import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut, User, Crown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Don't show navbar on auth pages
  if (!isAuthenticated) return null;

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
        {isAdmin && (
          <Link
            to="/admin"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              location.pathname === '/admin' ? "text-primary" : "text-muted-foreground"
            )}
          >
            Admin Dashboard
          </Link>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* User Info */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-full border border-white/5">
          <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
            {isAdmin ? (
              <Crown size={13} className="text-primary" />
            ) : (
              <User size={13} className="text-primary" />
            )}
          </div>
          <span className="text-xs font-medium text-foreground">{user?.username}</span>
          <span className={cn(
            "text-[9px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded-md",
            isAdmin
              ? "bg-primary/20 text-primary"
              : "bg-white/10 text-muted-foreground"
          )}>
            {user?.role}
          </span>
        </div>

        {/* Logout */}
        <Button
          variant="ghost"
          size="icon"
          onClick={handleLogout}
          className="hover:bg-destructive/20 hover:text-destructive text-muted-foreground transition-all"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </Button>
      </div>
    </nav>
  );
}
