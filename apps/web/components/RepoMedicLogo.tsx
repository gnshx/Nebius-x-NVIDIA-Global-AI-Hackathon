import React from 'react';

interface RepoMedicLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
  className?: string;
}

export function RepoMedicLogo({ size = 'md', showPulse = true, className = '' }: RepoMedicLogoProps) {
  const dimensions = {
    sm: 'w-7 h-7',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  }[size];

  const iconSizes = {
    sm: 16,
    md: 22,
    lg: 36,
  }[size];

  return (
    <div className={`relative inline-flex items-center justify-center shrink-0 ${className}`}>
      {/* Outer ambient glow */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-emerald-500/20 via-cyan-500/20 to-purple-500/20 blur-md -z-10" />

      {/* Main Container */}
      <div
        className={`${dimensions} rounded-xl bg-gradient-to-br from-zinc-900 via-zinc-950 to-black border border-emerald-500/30 flex items-center justify-center shadow-lg relative overflow-hidden group`}
      >
        {/* Subtle grid texture inside */}
        <div className="absolute inset-0 bg-tech-grid opacity-30" />

        {/* Diagonal sheen */}
        <div className="absolute -inset-full top-0 bg-gradient-to-r from-transparent via-white/5 to-transparent rotate-45 group-hover:translate-x-full transition-transform duration-1000" />

        {/* High-tech Emblem SVG: Medical Cross + Git Commit Graph */}
        <svg
          width={iconSizes}
          height={iconSizes}
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative z-10"
        >
          <defs>
            <linearGradient id="logoGrad" x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
              <stop stopColor="#10B981" />
              <stop offset="0.5" stopColor="#06B6D4" />
              <stop offset="1" stopColor="#8B5CF6" />
            </linearGradient>
            <linearGradient id="strokeGrad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
              <stop stopColor="#34D399" />
              <stop offset="1" stopColor="#38BDF8" />
            </linearGradient>
          </defs>

          {/* Central Medical Shield Path */}
          <path
            d="M16 3L6 7V15C6 21.5 10.3 27.5 16 29C21.7 27.5 26 21.5 26 15V7L16 3Z"
            stroke="url(#strokeGrad)"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="drop-shadow-sm"
          />

          {/* Medical Cross + Git Branch Node Integration */}
          {/* Vertical stem */}
          <path
            d="M16 10V22"
            stroke="url(#logoGrad)"
            strokeWidth="2.4"
            strokeLinecap="round"
          />
          {/* Horizontal crossbar */}
          <path
            d="M11 15H21"
            stroke="url(#logoGrad)"
            strokeWidth="2.4"
            strokeLinecap="round"
          />

          {/* Git Branch Nodes */}
          <circle cx="16" cy="10" r="2" fill="#10B981" />
          <circle cx="16" cy="22" r="2" fill="#06B6D4" />
          <circle cx="11" cy="15" r="1.8" fill="#34D399" />
          <circle cx="21" cy="15" r="1.8" fill="#8B5CF6" />
        </svg>

        {/* Live Active Status Dot */}
        {showPulse && (
          <span className="absolute top-1 right-1 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
        )}
      </div>
    </div>
  );
}
