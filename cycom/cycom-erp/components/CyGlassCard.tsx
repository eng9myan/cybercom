import React from 'react';

interface CyGlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverable?: boolean;
}

export function CyGlassCard({ children, className = '', hoverable = false, ...props }: CyGlassCardProps) {
  return (
    <div
      className={`
        backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-6 shadow-xl
        transition-all duration-300
        ${hoverable ? 'hover:bg-white/10 hover:border-white/20 hover:scale-[1.01]' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}
