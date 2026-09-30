import Link from 'next/link';
import { Activity, GitPullRequest, LayoutDashboard, Settings, Database } from 'lucide-react';

const navLinks = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/runs', label: 'Runs', icon: Activity },
  { href: '/repositories', label: 'Repositories', icon: Database },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Navbar() {
  return (
    <nav className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 font-bold text-lg hover:opacity-80 transition-opacity">
            <img src="/assets/logo.jpg" alt="RepoMedic Logo" className="w-7 h-7 rounded-lg object-cover shadow-sm" />
            <span>RepoMedic</span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
